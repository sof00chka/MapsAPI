import arcade
from arcade.gui import UIManager, UIFlatButton, UILabel, UIInputText
import requests
from PIL import Image
from io import BytesIO

MAP_SIZE = (650, 500)  # размеры png от яндекса
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
        self.light_theme = True  # переключатель темы карты, по умолчанию светлая
        self.points = []  # список для хранения всех меток
        self.error_message = ""
        self.success_message = ""
        self.message_timer = 0
        self.message_text = None
        self.show_postal_code = False
        self.update_map()

        self.setup_widgets()  # Функция ниже

    def setup_widgets(self):
        # UI - координаты ручками
        label = UILabel(y=SCREEN_HEIGHT - 50,
                        text="ll:",
                        font_size=20,
                        text_color=arcade.color.BLACK,
                        width=300, )
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

        label = UILabel(y=SCREEN_HEIGHT - 200,
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

        flat_button = UIFlatButton(text="Показать", width=200, height=50, color=arcade.color.BLUE, y=25)
        flat_button.on_click = lambda event: self.update_map()
        self.manager.add(flat_button)

        change_theme_button = UIFlatButton(text='Сменить тему', width=200, height=50, color=arcade.color.BLUE, y=90)
        change_theme_button.on_click = lambda event: self.change_theme()
        self.manager.add(change_theme_button)

        label = UILabel(y=SCREEN_HEIGHT - 370, text="Поиск объекта:", font_size=20, text_color=arcade.color.BLACK,
                        width=200)
        self.manager.add(label)
        self.search_input = UIInputText(y=SCREEN_HEIGHT - 420, width=250, height=30, text="",
                                        text_color=arcade.color.BLACK)
        self.manager.add(self.search_input)

        search_button = UIFlatButton(text='Искать', width=200, height=50, color=arcade.color.GREEN, y=155)
        search_button.on_click = lambda event: self.search_object()
        self.manager.add(search_button)

        clear_button = UIFlatButton(text='Сбросить', width=200, height=50, color=arcade.color.RED, y=220)
        clear_button.on_click = lambda event: self.clear_points()
        self.manager.add(clear_button)

        self.postal_code_button = UIFlatButton(text='Индекс: ВЫКЛ', width=200, height=50, color=arcade.color.GRAY,
                                               y=285)
        self.postal_code_button.on_click = lambda event: self.toggle_postal_code()
        self.manager.add(self.postal_code_button)

    def clear_points(self):
        self.points = []
        self.message_text = None
        self.success_message = ""
        self.error_message = ""
        self.update_map()

    def show_error(self, message):
        self.error_message = message
        self.success_message = ""
        self.message_timer = 180
        self.message_text = arcade.Text(
            message,
            SCREEN_WIDTH // 2,
            15,
            arcade.color.RED_DEVIL,
            font_size=14,
            anchor_x="center",
            anchor_y="center"
        )

    def show_success(self, message):
        self.success_message = message
        self.error_message = ""
        self.message_timer = 180
        self.message_text = arcade.Text(
            message,
            SCREEN_WIDTH // 2,
            15,
            arcade.color.GREEN,
            font_size=14,
            anchor_x="center",
            anchor_y="center"
        )

    def on_draw(self):
        self.clear()
        arcade.draw_texture_rect(self.Map, arcade.rect.XYWH(SCREEN_WIDTH - MAP_SIZE[0] * MAP_SCALE / 2 - MAP_BORDER,
                                                            SCREEN_HEIGHT / 2, MAP_SIZE[0] * MAP_SCALE,
                                                            MAP_SIZE[1] * MAP_SCALE))

        if self.message_text:
            self.message_text.draw()

        self.manager.draw()

    def toggle_postal_code(self):
        self.show_postal_code = not self.show_postal_code
        if self.show_postal_code:
            self.postal_code_button.text = 'Индекс: ВКЛ'
            self.postal_code_button.color = arcade.color.GREEN
        else:
            self.postal_code_button.text = 'Индекс: ВЫКЛ'
            self.postal_code_button.color = arcade.color.GRAY

        if self.points:
            self.update_points_addresses()

    def update_points_addresses(self):
        if not self.points:
            return

        geocoder_api_server = "http://geocode-maps.yandex.ru/1.x/"

        all_points_info = []
        for point in self.points:
            geocoder_params = {
                "apikey": "8013b162-6b42-4997-9691-77b7074026e0",
                "geocode": f"{point[0]},{point[1]}",
                "format": "json",
                "kind": "house",
                "results": "1"
            }

            try:
                response = requests.get(geocoder_api_server, params=geocoder_params)
                if response:
                    json_response = response.json()
                    feature_member = json_response["response"]["GeoObjectCollection"]["featureMember"]

                    if feature_member:
                        toponym = feature_member[0]["GeoObject"]
                        address = toponym["metaDataProperty"]["GeocoderMetaData"]["text"]

                        if self.show_postal_code:
                            postal_code = toponym["metaDataProperty"]["GeocoderMetaData"]["Address"].get("postal_code",
                                                                                                         "")
                            if postal_code:
                                address = f"{postal_code}, {address}"

                        all_points_info.append(address)
                    else:
                        all_points_info.append(f"{point[0]}, {point[1]}")
                else:
                    all_points_info.append(f"{point[0]}, {point[1]}")
            except Exception:
                all_points_info.append(f"{point[0]}, {point[1]}")

        if all_points_info:
            self.show_success(f"Найден: {all_points_info[-1]}")

    def search_object(self):
        query = self.search_input.text.strip()

        if not query:
            self.show_error("Введите запрос для поиска")
            return

        geocoder_api_server = "http://geocode-maps.yandex.ru/1.x/"
        geocoder_params = {
            "apikey": "8013b162-6b42-4997-9691-77b7074026e0",
            "geocode": query,
            "format": "json"
        }
        try:
            response = requests.get(geocoder_api_server, params=geocoder_params)

            if not response:
                self.show_error("Ошибка при обращении к геокодеру")
                return

            json_response = response.json()
            feature_member = json_response["response"]["GeoObjectCollection"]["featureMember"]

            if not feature_member:
                self.show_error(f"Объект '{query}' не найден")
                return

            # Получаем первый топоним из ответа геокодера
            toponym = feature_member[0]["GeoObject"]

            # Получаем координаты центра топонима
            toponym_coordinates = toponym["Point"]["pos"]
            toponym_longitude, toponym_latitude = toponym_coordinates.split(" ")

            toponym_name = toponym["metaDataProperty"]["GeocoderMetaData"]["text"]

            if self.show_postal_code:
                postal_code = toponym["metaDataProperty"]["GeocoderMetaData"]["Address"].get("postal_code", "")
                if postal_code:
                    toponym_name = f"{postal_code}, {toponym_name}"

            bbox = toponym.get("boundedBy", {}).get("Envelope", {})
            if bbox:
                lower_corner = bbox.get("lowerCorner", "").split()
                upper_corner = bbox.get("upperCorner", "").split()
                if len(lower_corner) == 2 and len(upper_corner) == 2:
                    new_min_lon = float(lower_corner[0])
                    new_min_lat = float(lower_corner[1])
                    new_max_lon = float(upper_corner[0])
                    new_max_lat = float(upper_corner[1])
                else:
                    new_min_lon = float(toponym_longitude)
                    new_min_lat = float(toponym_latitude)
                    new_max_lon = float(toponym_longitude)
                    new_max_lat = float(toponym_latitude)
            else:
                new_min_lon = float(toponym_longitude)
                new_min_lat = float(toponym_latitude)
                new_max_lon = float(toponym_longitude)
                new_max_lat = float(toponym_latitude)
            self.points.append((float(toponym_longitude), float(toponym_latitude)))

            if len(self.points) == 1:
                self.min_lon = new_min_lon
                self.min_lat = new_min_lat
                self.max_lon = new_max_lon
                self.max_lat = new_max_lat
            else:
                # Расширяем границы, если новый объект выходит за пределы
                self.min_lon = min(self.min_lon, new_min_lon)
                self.min_lat = min(self.min_lat, new_min_lat)
                self.max_lon = max(self.max_lon, new_max_lon)
                self.max_lat = max(self.max_lat, new_max_lat)

            self.ll = [(self.min_lon + self.max_lon) / 2, (self.min_lat + self.max_lat) / 2]

            delta_lon = self.max_lon - self.min_lon
            delta_lat = self.max_lat - self.min_lat

            if delta_lon == 0 and delta_lat == 0:
                self.spn = [0.005, 0.005]
            else:
                self.spn[0] = max(delta_lon * 1.2, 0.0001)
                self.spn[1] = max(delta_lat * 1.2, 0.0001)
                self.spn[0] = min(self.spn[0], 90.0)
                self.spn[1] = min(self.spn[1], 90.0)

            self.gui_elements[0].text = str(round(self.ll[0], 6))
            self.gui_elements[1].text = str(round(self.ll[1], 6))
            self.gui_elements[2].text = str(round(self.spn[0], 6))
            self.gui_elements[3].text = str(round(self.spn[1], 6))

            self.update_map()

            self.show_success(f"Найден: {toponym_name}")

        except Exception as e:
            self.show_error(f"Ошибка при поиске: {str(e)}")

    def update_map(self):
        api_server = "https://static-maps.yandex.ru/v1"

        if self.light_theme:
            text = 'light'
        else:
            text = 'dark'

        params = {
            'll': ",".join(map(str, self.ll)),
            'spn': ','.join(map(str, self.spn)),
            'apikey': 'f3a0fe3a-b07e-4840-a1da-06f18b2ddf13',
            'theme': text,
            'size': '600,450'
        }

        if self.points:
            points_str = []
            for i, p in enumerate(self.points):
                if i == len(self.points) - 1:
                    points_str.append(f"{p[0]},{p[1]},pm2rdm")
                else:
                    points_str.append(f"{p[0]},{p[1]},pm2blm")
            params['pt'] = "~".join(points_str)

        try:
            response = requests.get(api_server, params=params)
            if not response:
                self.show_error("Ошибка при загрузке карты")
                return

            image = Image.open(BytesIO(response.content))
            image = image.convert("RGBA")
            self.Map = arcade.Texture(image)
        except Exception as e:
            self.show_error(f"Ошибка при загрузке карты: {str(e)}")

    def ll_change(self, value, a):
        try:
            if value.new_value == '':
                self.ll[a] = 0
            else:
                self.ll[a] = float(value.new_value)
        except ValueError:
            self.gui_elements[a].text = value.old_value
            self.show_error("Некорректный формат координат")

    def spn_change(self, value, a):
        try:
            if value.new_value == '':
                self.spn[a] = 0
            else:
                self.spn[a] = float(value.new_value)
        except ValueError:
            self.gui_elements[a + 2].text = value.old_value
            self.show_error("Некорректный формат масштаба")

    def on_key_press(self, key, modifiers):
        # коэф-нт изменения масштаба (можно поменять потом)
        zoom_step = 2.0

        # Поиск
        if key == arcade.key.ENTER:
            self.search_object()
            return

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
        #  шаг перемещения (10% от текущего spn)
        move_step_lon = self.spn[0] * 0.1
        move_step_lat = self.spn[1] * 0.1
        if key == arcade.key.UP:
            # Перемещаем на север (увеличиваем широту)
            new_lat = self.ll[1] + move_step_lat
            if new_lat <= MAX_LAT:
                self.ll[1] = new_lat
            else:
                self.show_error("Достигнута северная граница")
        elif key == arcade.key.DOWN:
            # Перемещаем на юг (уменьшаем широту)
            new_lat = self.ll[1] - move_step_lat
            if new_lat >= MIN_LAT:
                self.ll[1] = new_lat
            else:
                self.show_error("Достигнута южная граница")
        elif key == arcade.key.LEFT:
            # Перемещаем на запад (уменьшаем долготу)
            new_lon = self.ll[0] - move_step_lon
            if new_lon >= MIN_LON:
                self.ll[0] = new_lon
            else:
                self.show_error("Достигнута западная граница")
        elif key == arcade.key.RIGHT:
            # Перемещаем на восток (увеличиваем долготу)
            new_lon = self.ll[0] + move_step_lon
            if new_lon <= MAX_LON:
                self.ll[0] = new_lon
            else:
                self.show_error("Достигнута восточная граница")
        else:
            return  # Не обновляем карту, если нажата не та клавиша
        # Обновляем значения в полях ввода
        self.gui_elements[0].text = str(self.ll[0])
        self.gui_elements[1].text = str(self.ll[1])
        # Обновляем карту
        self.update_map()

    def sync_ui_and_update(self):
        # поля ввода меняются
        self.gui_elements[2].text = str(round(self.spn[0], 6))
        self.gui_elements[3].text = str(round(self.spn[1], 6))
        self.update_map()

    def change_theme(self):
        self.light_theme = not self.light_theme
        self.update_map()


if __name__ == "__main__":
    game = MyGUIWindow()
    arcade.run()