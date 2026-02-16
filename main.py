import arcade
from arcade.gui import UIManager, UIFlatButton, UILabel, UIInputText
import requests
from PIL import Image
from io import BytesIO

MAP_SIZE = (600, 450)  # размеры png от яндекса
MAP_SCALE = 1.5  # увелечение png
SCREEN_WIDTH = MAP_SIZE[0] * MAP_SCALE + 300
MAP_BORDER = 25
SCREEN_HEIGHT = MAP_SIZE[1] * MAP_SCALE + MAP_BORDER * 2

# Границы координат
MIN_LON = 30.0
MAX_LON = 45.0
MIN_LAT = 50.0
MAX_LAT = 65.0


class MyGUIWindow(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, "Яндекс карты")
        arcade.set_background_color(arcade.color.GRAY)

        self.manager = UIManager()
        self.manager.enable()
        self.gui_elements = []  # для изменение текста в UIInputText

        self.ll = [37.677751, 55.757718]
        self.spn = [0.016457, 0.00619]
        self.Map = None
        self.update_map()

        self.setup_widgets()  # Функция ниже

    def setup_widgets(self):
        # UI - координаты ручками
        label = UILabel(y=SCREEN_HEIGHT - 50,
                        text="ll:",
                        font_size=20,
                        text_color=arcade.color.BLACK,
                        width=300,)
        self.manager.add(label)

        input_text = UIInputText(y=SCREEN_HEIGHT - 100,
                                 width=200,
                                 height=30,
                                 text=str(self.ll[0]),
                                 text_color=arcade.color.BLACK)
        input_text.on_change = lambda text: self.ll_change(text, 0)
        self.manager.add(input_text)
        self.gui_elements.append(input_text)

        input_text = UIInputText(y=SCREEN_HEIGHT - 150,
                                 width=200,
                                 height=30,
                                 text=str(self.ll[1]),
                                 text_color=arcade.color.BLACK)
        input_text.on_change = lambda text: self.ll_change(text, 1)
        self.manager.add(input_text)
        self.gui_elements.append(input_text)

        label = UILabel(y = SCREEN_HEIGHT - 200,
                        text="spn:",
                        font_size=20,
                        text_color=arcade.color.BLACK,
                        width=300)
        self.manager.add(label)

        input_text = UIInputText(y=SCREEN_HEIGHT - 250,
                                 width=200,
                                 height=30,
                                 text=str(self.spn[0]),
                                 text_color=arcade.color.BLACK)
        input_text.on_change = lambda text: self.spn_change(text, 0)
        self.manager.add(input_text)
        self.gui_elements.append(input_text)

        input_text = UIInputText(y=SCREEN_HEIGHT - 300,
                                 width=200,
                                 height=30,
                                 text=str(self.spn[1]),
                                 text_color=arcade.color.BLACK)
        input_text.on_change = lambda text: self.spn_change(text, 1)
        self.manager.add(input_text)
        self.gui_elements.append(input_text)

        flat_button = UIFlatButton(text="показать", width=200, height=50, color=arcade.color.BLUE, y = 25)
        flat_button.on_click = lambda event: self.update_map()
        self.manager.add(flat_button)

    def on_draw(self):
        self.clear()
        arcade.draw_texture_rect(self.Map, arcade.rect.XYWH(SCREEN_WIDTH - MAP_SIZE[0] * MAP_SCALE / 2 - MAP_BORDER,
                                                            SCREEN_HEIGHT / 2,
                                                            MAP_SIZE[0] * MAP_SCALE, MAP_SIZE[1] * MAP_SCALE))
        self.manager.draw()

    def update_map(self):
        api_server = "https://static-maps.yandex.ru/v1"
        # параметр scale, отвечающий за размер, по умолчанию максимально возможное 600x450
        params = {
            'll': ",".join(map(str, self.ll)),
            'spn': ','.join(map(str, self.spn)),
            'apikey': 'f3a0fe3a-b07e-4840-a1da-06f18b2ddf13'
        }
        response = requests.get(api_server, params=params)
        if not response:
            raise Exception('ошибка с запросом')

        # этот способ намного быстрее сохранения картинки отдельно
        # этим способом хоть какая-то плавность при быстром изенении карты (пункт 2 и 3)
        image = Image.open(BytesIO(response.content))
        image = image.convert("RGBA")
        self.Map = arcade.Texture(image)

    def ll_change(self, value, a):
        try:
            if value.new_value == '':
                self.ll[a] = 0
            else:
                self.ll[a] = float(value.new_value)
        except ValueError:
            self.gui_elements[a].text = value.old_value

    def spn_change(self, value, a):
        try:
            if value.new_value == '':
                self.spn[a] = 0
            else:
                self.spn[a] = float(value.new_value)
        except ValueError:
            self.gui_elements[a + 2].text = value.old_value

    def on_key_press(self, key, modifiers):
        # Вычисляем шаг перемещения (10% от текущего spn)
        move_step_lon = self.spn[0] * 0.1
        move_step_lat = self.spn[1] * 0.1
        if key == arcade.key.UP:
            # Перемещаем на север (увеличиваем широту)
            self.ll[1] = min(self.ll[1] + move_step_lat, MAX_LAT)
        elif key == arcade.key.DOWN:
            # Перемещаем на юг (уменьшаем широту)
            self.ll[1] = max(self.ll[1] - move_step_lat, MIN_LAT)
        elif key == arcade.key.LEFT:
            # Перемещаем на запад (уменьшаем долготу)
            self.ll[0] = max(self.ll[0] - move_step_lon, MIN_LON)
        elif key == arcade.key.RIGHT:
            # Перемещаем на восток (увеличиваем долготу)
            self.ll[0] = min(self.ll[0] + move_step_lon, MAX_LON)
        else:
            return  # Не обновляем карту, если нажата не та клавиша
        # Обновляем значения в полях ввода
        self.gui_elements[0].text = str(self.ll[0])
        self.gui_elements[1].text = str(self.ll[1])
        # Обновляем карту
        self.update_map()

    def on_key_press(self, key, modifiers):
        # коэф-нт изменения масштаба (можно поменять потом)
        zoom_step = 2.0

        if key == arcade.key.PAGEUP:
            # spn (приближаем)
            self.spn[0] = max(self.spn[0] / zoom_step, 0.0001)
            self.spn[1] = max(self.spn[1] / zoom_step, 0.0001)
            self.sync_ui_and_update()

        elif key == arcade.key.PAGEDOWN:
            #  spn (отдаляем)
            self.spn[0] = min(self.spn[0] * zoom_step, 90.0)
            self.spn[1] = min(self.spn[1] * zoom_step, 90.0)
            self.sync_ui_and_update()

    def sync_ui_and_update(self):
        # поля ввода меняются
        self.gui_elements[2].text = str(round(self.spn[0], 6))
        self.gui_elements[3].text = str(round(self.spn[1], 6))
        self.update_map()


if __name__ == "__main__":
    game = MyGUIWindow()
    arcade.run()
