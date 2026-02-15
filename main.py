import arcade
from arcade.gui import UIManager, UIFlatButton, UITextureButton, UILabel, UIInputText, UITextArea, UISlider, UIDropdown, \
    UIMessageBox  # Это разные виджеты
from arcade.gui.widgets.layout import UIAnchorLayout, UIBoxLayout  # А это менеджеры компоновки, как в pyQT

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600


class MyGUIWindow(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, "Супер GUI Пример!")
        arcade.set_background_color(arcade.color.GRAY)

        # UIManager — сердце GUI
        self.manager = UIManager()
        self.manager.enable()  # Включить, чтоб виджеты работали

        # Layout для организации — как полки в шкафу
        self.anchor_layout = UIAnchorLayout()  # Центрирует виджеты
        self.box_layout = UIBoxLayout(vertical=True, space_between=10)  # Вертикальный стек

        # Добавим все виджеты в box, потом box в anchor
        self.setup_widgets()  # Функция ниже

        self.anchor_layout.add(self.box_layout)  # Box в anchor
        self.manager.add(self.anchor_layout)  # Всё в manager

    def setup_widgets(self):
        text_area = UITextArea(text="Это UITextArea.\nМного строк!\nДля логов или чата.\nИли блога про своего котика",
                               width=200,
                               height=100,
                               font_size=14)
        self.anchor_layout.add(text_area)

        label = UILabel(text="Привет, Мир! Это UILabel",
                        font_size=20,
                        text_color=arcade.color.WHITE,
                        width=300,
                        align="center")
        self.anchor_layout.add(label)

    def on_draw(self):
        self.clear()
        self.manager.draw()  # Рисуй GUI поверх всего

    def on_mouse_press(self, x, y, button, modifiers):
        pass  # Для кликов, но manager сам обрабатывает


if __name__ == "__main__":
    game = MyGUIWindow()
    arcade.run()
