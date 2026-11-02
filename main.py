Python 3.15.0 (tags/v3.15.0:d220409, Oct  9 2026, 11:55:56) [MSC v.1951 64 bit (AMD64)] on win32
Enter "help" below or click "Help" above for more information.
from kivy.app import App
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, Ellipse
from kivy.config import Config
from kivy.utils import platform
import random

# Отключаем закрытие по Esc (шутка, но в Kivy можно)
Config.set('kivy', 'exit_on_escape', '0')

# --- Пароль ---
SECRET_CODE = "0000"


class Particle:
    __slots__ = ("x", "y", "sx", "sy", "r")

    def __init__(self, w, h):
        self.x = random.uniform(0, w)
        self.y = random.uniform(0, h)
        self.sx = random.uniform(-0.7, 0.7) * 60  # в пикселях/сек
        self.sy = random.uniform(-0.7, 0.7) * 60
        self.r = random.uniform(1.0, 1.8)


class Background(Widget):
    """Чёрно-красный градиент + летающие точки."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.particles = []
        self._dt_accum = 0
        self.bind(size=self._redraw_bg, pos=self._redraw_bg)
        Clock.schedule_interval(self._update, 1 / 30)

    def _redraw_bg(self, *args):
        w, h = self.size
        if w <= 1 or h <= 1:
            return
        # Плавный градиент от тёмно-красного сверху к чёрному снизу
        self.canvas.before.clear()
        steps = 40
        with self.canvas.before:
            for i in range(steps):
                t = i / steps
                r = int(40 * (1 - t)) / 255.0
                Rectangle(
                    pos=(self.x, self.y + h * (1 - (i + 1) / steps)),
                    size=(w, h / steps + 1),
                    source=None,
                )
                Color(r, 0.0, 0.0, 1)
        self._create_particles()

    def _create_particles(self):
        w, h = self.size
        self.particles = [Particle(w, h) for _ in range(120)]

    def _update(self, dt):
        w, h = self.size
        if w <= 1:
            return
        for p in self.particles:
            p.x += p.sx * dt
            p.y += p.sy * dt
            if p.x < 0:
                p.x += w
            elif p.x > w:
                p.x -= w
            if p.y < 0:
                p.y += h
            elif p.y > h:
                p.y -= h

        self.canvas.after.clear()
        with self.canvas.after:
            Color(1, 1, 1, 1)
            for p in self.particles:
                Ellipse(pos=(self.x + p.x, self.y + p.y), size=(p.r * 2, p.r * 2))


class LockerUI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        self.time_left = 12 * 3600  # 12 часов
        self.error = False

        self.spacer_top = Widget(size_hint=(1, 0.15))
        self.add_widget(self.spacer_top)

        # Карточка
        self.card = BoxLayout(
            orientation="vertical",
            size_hint=(None, None),
            width=min(Window.width * 0.9, 620),
            height=700,
            pos_hint={"center_x": 0.5},
            padding=[40, 30, 40, 30],
            spacing=12,
        )
        self.add_widget(self.card)
        self.spacer_bottom = Widget(size_hint=(1, 0.15))
        self.add_widget(self.spacer_bottom)

        # Красная рамка вокруг карточки
        with self.card.canvas.before:
            self._border_color = Color(0.8, 0.0, 0.0, 1)
            self._border_rect = Rectangle(pos=self.card.pos, size=self.card.size)
        with self.card.canvas.before:
            # Внутренняя заливка поверх рамки (эмулируем рамку 2px)
            pass
        self._inner_color_instruction = None
        self._inner_rect_instruction = None
        with self.card.canvas:
            self._inner_color_instruction = Color(0.067, 0.067, 0.067, 1)
            self._inner_rect_instruction = Rectangle(pos=self.card.pos, size=self.card.size)

        self.card.bind(pos=self._sync_card, size=self._sync_card)

        # 💀
        self.icon = Label(
            text="💀",
            font_size="90sp",
            color=(0.8, 0, 0, 1),
            size_hint=(1, None),
            height=110,
            markup=False,
        )
        self.card.add_widget(self.icon)

        # Заголовок
        self.title = Label(
            text="ВНИМАНИЕ! СИСТЕМА ЗАРАЖЕНА",
            font_size="28sp",
            bold=True,
            color=(0.8, 0, 0, 1),
            size_hint=(1, None),
            height=45,
        )
        self.card.add_widget(self.title)

        # Подзаголовок
        self.subtitle = Label(
            text="Ваши файлы зашифрованы.\n"
                 "Для восстановления доступа введите код.\n"
                 "Осталось времени:",
            font_size="16sp",
            color=(0.7, 0.7, 0.7, 1),
            halign="center",
            valign="middle",
            size_hint=(1, None),
            height=75,
        )
        self.subtitle.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        self.card.add_widget(self.subtitle)

        # Таймер
        self.timer = Label(
            text="12:00:00",
            font_size="72sp",
            bold=True,
            color=(1, 1, 1, 1),
            size_hint=(1, None),
            height=100,
        )
        self.card.add_widget(self.timer)

        # Поле ввода
        self.entry = TextInput(
            text="",
            hint_text="Введите ключ...",
            font_size="20sp",
            multiline=False,
            halign="center",
            input_type="number",
            size_hint=(1, None),
            height=60,
            background_color=(0.1, 0, 0, 1),
            foreground_color=(1, 1, 1, 1),
            cursor_color=(0.8, 0, 0, 1),
            padding=[10, 18, 10, 10],
        )
        self.entry.bind(on_text_validate=self.check_code)
        self.card.add_widget(self.entry)

        # Ошибка
        self.error_label = Label(
            text="",
            font_size="14sp",
            bold=True,
            color=(1, 0.2, 0.2, 1),
            size_hint=(1, None),
            height=30,
        )
        self.card.add_widget(self.error_label)

        # Кнопка
        self.btn = Button(
            text="РАСШИФРОВАТЬ",
            font_size="20sp",
            bold=True,
            size_hint=(1, None),
            height=60,
            background_color=(0.8, 0, 0, 1),
            background_normal="",
        )
        self.btn.bind(on_release=self.check_code)
        self.card.add_widget(self.btn)

        # Таймер
        Clock.schedule_interval(self.update_timer, 1.0)
        Clock.schedule_once(lambda dt: setattr(self.entry, "focus", True), 0.2)
        # Автофокус (анти-alt-tab)
        Clock.schedule_interval(self.keep_focus, 0.1)

    def _sync_card(self, instance, value):
        self._border_rect.pos = (instance.x - 2, instance.y - 2)
        self._border_rect.size = (instance.width + 4, instance.height + 4)
        self._inner_rect_instruction.pos = instance.pos
        self._inner_rect_instruction.size = instance.size

    def update_timer(self, dt):
        if self.time_left < 0:
            return False
        h = self.time_left // 3600
        m = (self.time_left % 3600) // 60
        s = self.time_left % 60
        self.timer.text = f"{h:02d}:{m:02d}:{s:02d}"
        self.time_left -= 1

    def check_code(self, *args):
        if self.entry.text.strip() == SECRET_CODE:
            App.get_running_app().stop()
            Window.close()
        else:
            self.entry.text = ""
            self.error_label.text = "❌ НЕВЕРНЫЙ КОД."
            self.entry.focus = True

    def keep_focus(self, dt):
        if not self.entry.focus:
            try:
                self.entry.focus = True
            except Exception:
                pass


class LockerApp(App):
    def build(self):
        # Полноэкранный режим
        if platform in ("android", "ios"):
            Window.fullscreen = True
        else:
            Window.fullscreen = "auto"

        Window.clearcolor = (0.02, 0.02, 0.02, 1)
        # Пытаемся убрать заголовок на десктопе (на Android не нужно)
        Window.borderless = True
        Window.size = (Window.width, Window.height)

        root = BoxLayout(orientation="vertical")
        bg = Background()
        # Кладём фон и UI в один родитель (можно через FloatLayout)
        from kivy.uix.floatlayout import FloatLayout
        float_root = FloatLayout()
        float_root.add_widget(bg)
        ui = LockerUI(size_hint=(1, 1))
        float_root.add_widget(ui)

        # Перехват "Назад" (Android)
        Window.bind(on_keyboard=self.on_key_down)
        return float_root

    def on_key_down(self, window, key, *args):
        # key == 27 — Esc/Back на Android
        if key == 27:
            # Не даём выйти
            return True
        return False

    def on_pause(self):
        # Не даём свернуть приложение
        return True

    def on_resume(self):
        pass


if __name__ == "__main__":
    LockerApp().run()from kivy.app import App
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, Ellipse
from kivy.config import Config
from kivy.utils import platform
import random

# Отключаем закрытие по Esc (шутка, но в Kivy можно)
Config.set('kivy', 'exit_on_escape', '0')

# --- Пароль ---
SECRET_CODE = "0000"


class Particle:
    __slots__ = ("x", "y", "sx", "sy", "r")

    def __init__(self, w, h):
        self.x = random.uniform(0, w)
        self.y = random.uniform(0, h)
        self.sx = random.uniform(-0.7, 0.7) * 60  # в пикселях/сек
        self.sy = random.uniform(-0.7, 0.7) * 60
        self.r = random.uniform(1.0, 1.8)


class Background(Widget):
    """Чёрно-красный градиент + летающие точки."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.particles = []
        self._dt_accum = 0
        self.bind(size=self._redraw_bg, pos=self._redraw_bg)
        Clock.schedule_interval(self._update, 1 / 30)

    def _redraw_bg(self, *args):
        w, h = self.size
        if w <= 1 or h <= 1:
            return
        # Плавный градиент от тёмно-красного сверху к чёрному снизу
        self.canvas.before.clear()
        steps = 40
        with self.canvas.before:
            for i in range(steps):
                t = i / steps
                r = int(40 * (1 - t)) / 255.0
                Rectangle(
                    pos=(self.x, self.y + h * (1 - (i + 1) / steps)),
                    size=(w, h / steps + 1),
                    source=None,
                )
                Color(r, 0.0, 0.0, 1)
        self._create_particles()

    def _create_particles(self):
        w, h = self.size
        self.particles = [Particle(w, h) for _ in range(120)]

    def _update(self, dt):
        w, h = self.size
        if w <= 1:
            return
        for p in self.particles:
            p.x += p.sx * dt
            p.y += p.sy * dt
            if p.x < 0:
                p.x += w
            elif p.x > w:
                p.x -= w
            if p.y < 0:
                p.y += h
            elif p.y > h:
                p.y -= h

        self.canvas.after.clear()
        with self.canvas.after:
            Color(1, 1, 1, 1)
            for p in self.particles:
                Ellipse(pos=(self.x + p.x, self.y + p.y), size=(p.r * 2, p.r * 2))


class LockerUI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        self.time_left = 12 * 3600  # 12 часов
        self.error = False

        self.spacer_top = Widget(size_hint=(1, 0.15))
        self.add_widget(self.spacer_top)

        # Карточка
        self.card = BoxLayout(
            orientation="vertical",
            size_hint=(None, None),
            width=min(Window.width * 0.9, 620),
            height=700,
            pos_hint={"center_x": 0.5},
            padding=[40, 30, 40, 30],
            spacing=12,
        )
        self.add_widget(self.card)
        self.spacer_bottom = Widget(size_hint=(1, 0.15))
        self.add_widget(self.spacer_bottom)

        # Красная рамка вокруг карточки
        with self.card.canvas.before:
            self._border_color = Color(0.8, 0.0, 0.0, 1)
            self._border_rect = Rectangle(pos=self.card.pos, size=self.card.size)
        with self.card.canvas.before:
            # Внутренняя заливка поверх рамки (эмулируем рамку 2px)
            pass
        self._inner_color_instruction = None
        self._inner_rect_instruction = None
        with self.card.canvas:
            self._inner_color_instruction = Color(0.067, 0.067, 0.067, 1)
            self._inner_rect_instruction = Rectangle(pos=self.card.pos, size=self.card.size)

        self.card.bind(pos=self._sync_card, size=self._sync_card)

        # 💀
        self.icon = Label(
            text="💀",
            font_size="90sp",
            color=(0.8, 0, 0, 1),
            size_hint=(1, None),
            height=110,
            markup=False,
        )
        self.card.add_widget(self.icon)

        # Заголовок
        self.title = Label(
            text="ВНИМАНИЕ! СИСТЕМА ЗАРАЖЕНА",
            font_size="28sp",
            bold=True,
            color=(0.8, 0, 0, 1),
            size_hint=(1, None),
            height=45,
        )
        self.card.add_widget(self.title)

        # Подзаголовок
        self.subtitle = Label(
            text="Ваши файлы зашифрованы.\n"
                 "Для восстановления доступа введите код.\n"
                 "Осталось времени:",
            font_size="16sp",
            color=(0.7, 0.7, 0.7, 1),
            halign="center",
            valign="middle",
            size_hint=(1, None),
            height=75,
        )
        self.subtitle.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        self.card.add_widget(self.subtitle)

        # Таймер
        self.timer = Label(
            text="12:00:00",
            font_size="72sp",
            bold=True,
            color=(1, 1, 1, 1),
            size_hint=(1, None),
            height=100,
        )
        self.card.add_widget(self.timer)

        # Поле ввода
        self.entry = TextInput(
            text="",
            hint_text="Введите ключ...",
            font_size="20sp",
            multiline=False,
            halign="center",
            input_type="number",
            size_hint=(1, None),
            height=60,
            background_color=(0.1, 0, 0, 1),
            foreground_color=(1, 1, 1, 1),
            cursor_color=(0.8, 0, 0, 1),
            padding=[10, 18, 10, 10],
        )
        self.entry.bind(on_text_validate=self.check_code)
        self.card.add_widget(self.entry)

        # Ошибка
        self.error_label = Label(
            text="",
            font_size="14sp",
            bold=True,
            color=(1, 0.2, 0.2, 1),
            size_hint=(1, None),
            height=30,
        )
        self.card.add_widget(self.error_label)

        # Кнопка
        self.btn = Button(
            text="РАСШИФРОВАТЬ",
            font_size="20sp",
            bold=True,
            size_hint=(1, None),
            height=60,
            background_color=(0.8, 0, 0, 1),
            background_normal="",
        )
        self.btn.bind(on_release=self.check_code)
        self.card.add_widget(self.btn)

        # Таймер
        Clock.schedule_interval(self.update_timer, 1.0)
        Clock.schedule_once(lambda dt: setattr(self.entry, "focus", True), 0.2)
        # Автофокус (анти-alt-tab)
        Clock.schedule_interval(self.keep_focus, 0.1)

    def _sync_card(self, instance, value):
        self._border_rect.pos = (instance.x - 2, instance.y - 2)
        self._border_rect.size = (instance.width + 4, instance.height + 4)
        self._inner_rect_instruction.pos = instance.pos
        self._inner_rect_instruction.size = instance.size

    def update_timer(self, dt):
        if self.time_left < 0:
            return False
        h = self.time_left // 3600
        m = (self.time_left % 3600) // 60
        s = self.time_left % 60
        self.timer.text = f"{h:02d}:{m:02d}:{s:02d}"
        self.time_left -= 1

    def check_code(self, *args):
        if self.entry.text.strip() == SECRET_CODE:
            App.get_running_app().stop()
            Window.close()
        else:
            self.entry.text = ""
            self.error_label.text = "❌ НЕВЕРНЫЙ КОД."
            self.entry.focus = True

    def keep_focus(self, dt):
        if not self.entry.focus:
            try:
                self.entry.focus = True
            except Exception:
                pass


class LockerApp(App):
    def build(self):
        # Полноэкранный режим
...         if platform in ("android", "ios"):
...             Window.fullscreen = True
...         else:
...             Window.fullscreen = "auto"
... 
...         Window.clearcolor = (0.02, 0.02, 0.02, 1)
...         # Пытаемся убрать заголовок на десктопе (на Android не нужно)
...         Window.borderless = True
...         Window.size = (Window.width, Window.height)
... 
...         root = BoxLayout(orientation="vertical")
...         bg = Background()
...         # Кладём фон и UI в один родитель (можно через FloatLayout)
...         from kivy.uix.floatlayout import FloatLayout
...         float_root = FloatLayout()
...         float_root.add_widget(bg)
...         ui = LockerUI(size_hint=(1, 1))
...         float_root.add_widget(ui)
... 
...         # Перехват "Назад" (Android)
...         Window.bind(on_keyboard=self.on_key_down)
...         return float_root
... 
...     def on_key_down(self, window, key, *args):
...         # key == 27 — Esc/Back на Android
...         if key == 27:
...             # Не даём выйти
...             return True
...         return False
... 
...     def on_pause(self):
...         # Не даём свернуть приложение
...         return True
... 
...     def on_resume(self):
...         pass
... 
... 
... if __name__ == "__main__":
