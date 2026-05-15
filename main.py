import math

import arcade
from arcade.gui import UIManager, UIFlatButton, UILabel, UIInputText
import requests
from PIL import Image
from io import BytesIO

# API ключи
STATIC_MAPS_API_KEY = 'f3a0fe3a-b07e-4840-a1da-06f18b2ddf13'
GEOCODER_API_KEY = '8013b162-6b42-4997-9691-77b7074026e0'
SEARCH_API_KEY = 'dda3ddba-c9ea-4ead-9010-f43fbc15c6e3'

MAP_SIZE = (650, 500)  # размеры PNG от Яндекса
MAP_SCALE = 1.5  # увеличение PNG
SCREEN_WIDTH = MAP_SIZE[0] * MAP_SCALE + 300
MAP_BORDER = 25
SCREEN_HEIGHT = MAP_SIZE[1] * MAP_SCALE + MAP_BORDER * 2 + 25

# Границы координат
MIN_LON = 30.0
MAX_LON = 45.0
MIN_LAT = 50.0
MAX_LAT = 65.0


class MyGUIWindow(arcade.Window):
    def __init__(self):
        self.session = requests.Session()  # reuse соединений для ускорения

        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, "Яндекс карты")
        arcade.set_background_color(arcade.color.GRAY)

        self.manager = UIManager()
        self.manager.enable()
        self.gui_elements = []  # для изменения текста в UIInputText

        self.ll = [37.677751, 55.757718]
        self.spn = [0.016457, 0.00619]
        self.Map = None
        self.light_theme = True

        # Типы карты для переключения
        self.map_types = ['map', 'driving', 'transit', 'admin']
        self.map_type_names = ['Базовая', 'Навигация', 'Транспорт', 'Админ']
        self.current_map_type_index = 0

        self.points = []  # список всех меток
        self.error_message = ""
        self.success_message = ""
        self.message_timer = 0
        self.message_text = None
        self.show_postal_code = False
        self.update_map()

        self.setup_widgets()

    def setup_widgets(self):
        label = UILabel(y=SCREEN_HEIGHT - 50, text="ll:", font_size=20,
                        text_color=arcade.color.BLACK, width=300)
        self.manager.add(label)

        input_text = UIInputText(y=SCREEN_HEIGHT - 100, width=200, height=30,
                                 text=str(self.ll[0]), text_color=arcade.color.BLACK)
        input_text.on_change = lambda text: self.ll_change(text, 0)
        self.manager.add(input_text)
        self.gui_elements.append(input_text)

        input_text = UIInputText(y=SCREEN_HEIGHT - 150, width=200, height=30,
                                 text=str(self.ll[1]), text_color=arcade.color.BLACK)
        input_text.on_change = lambda text: self.ll_change(text, 1)
        self.manager.add(input_text)
        self.gui_elements.append(input_text)

        label = UILabel(y=SCREEN_HEIGHT - 200, text="spn:", font_size=20,
                        text_color=arcade.color.BLACK, width=300)
        self.manager.add(label)

        input_text = UIInputText(y=SCREEN_HEIGHT - 250, width=200, height=30,
                                 text=str(self.spn[0]), text_color=arcade.color.BLACK)
        input_text.on_change = lambda text: self.spn_change(text, 0)
        self.manager.add(input_text)
        self.gui_elements.append(input_text)

        input_text = UIInputText(y=SCREEN_HEIGHT - 300, width=200, height=30,
                                 text=str(self.spn[1]), text_color=arcade.color.BLACK)
        input_text.on_change = lambda text: self.spn_change(text, 1)
        self.manager.add(input_text)
        self.gui_elements.append(input_text)

        # Кнопка "Показать"
        flat_button = UIFlatButton(text="Показать", width=200, height=50,
                                   color=arcade.color.BLUE, y=25)
        flat_button.on_click = lambda event: self.update_map()
        self.manager.add(flat_button)

        # Кнопка смены темы
        change_theme_button = UIFlatButton(text='Сменить тему', width=200, height=50,
                                           color=arcade.color.BLUE, y=90)
        change_theme_button.on_click = lambda event: self.change_theme()
        self.manager.add(change_theme_button)

        # Поиск объекта
        label = UILabel(y=SCREEN_HEIGHT - 370, text="Поиск объекта:", font_size=20,
                        text_color=arcade.color.BLACK, width=200)
        self.manager.add(label)
        self.search_input = UIInputText(y=SCREEN_HEIGHT - 420, width=250, height=30,
                                        text="", text_color=arcade.color.BLACK)
        self.manager.add(self.search_input)

        search_button = UIFlatButton(text='Искать', width=200, height=50,
                                     color=arcade.color.GREEN, y=155)
        search_button.on_click = lambda event: self.search_object()
        self.manager.add(search_button)

        # Сброс результата
        clear_button = UIFlatButton(text='Сбросить', width=200, height=50,
                                    color=arcade.color.RED, y=220)
        clear_button.on_click = lambda event: self.clear_points()
        self.manager.add(clear_button)

        # Переключатель почтового индекса
        self.postal_code_button = UIFlatButton(text='Индекс: ВЫКЛ', width=200, height=50,
                                               color=arcade.color.GRAY, y=285)
        self.postal_code_button.on_click = lambda event: self.toggle_postal_code()
        self.manager.add(self.postal_code_button)

        # Переключатель вида карты
        self.map_type_button = UIFlatButton(
            text=f'Вид: {self.map_type_names[self.current_map_type_index]}',
            width=200,
            height=50,
            color=arcade.color.ORANGE,
            y=350
        )
        self.map_type_button.on_click = lambda event: self.change_map_type()
        self.manager.add(self.map_type_button)

    def change_map_type(self):
        self.current_map_type_index = (self.current_map_type_index + 1) % len(self.map_types)
        self.map_type_button.text = f'Вид: {self.map_type_names[self.current_map_type_index]}'
        self.update_map()

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
        self.message_text = arcade.Text(message, SCREEN_WIDTH // 2, 15,
                                        arcade.color.RED_DEVIL, font_size=14,
                                        anchor_x="center", anchor_y="center")

    def show_success(self, message):
        self.success_message = message
        self.error_message = ""
        self.message_timer = 180
        self.message_text = arcade.Text(message, SCREEN_WIDTH // 2, 15,
                                        arcade.color.GREEN, font_size=14,
                                        anchor_x="center", anchor_y="center")

    def on_draw(self):
        self.clear()
        arcade.draw_texture_rect(self.Map,
                                 arcade.rect.XYWH(SCREEN_WIDTH - MAP_SIZE[0] * MAP_SCALE / 2 - MAP_BORDER,
                                                  SCREEN_HEIGHT / 2,
                                                  MAP_SIZE[0] * MAP_SCALE,
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
                "apikey": GEOCODER_API_KEY,
                "geocode": f"{point[0]},{point[1]}",
                "format": "json",
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

    def search_object(self, spn_flag=True):
        self.clear_points()
        query = self.search_input.text.strip()
        if not query:
            self.show_error("Введите запрос для поиска")
            return

        geocoder_api_server = "http://geocode-maps.yandex.ru/1.x/"
        geocoder_params = {
            "apikey": GEOCODER_API_KEY,
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

            toponym = feature_member[0]["GeoObject"]
            toponym_coordinates = toponym["Point"]["pos"]
            toponym_longitude, toponym_latitude = toponym_coordinates.split(" ")

            obj_lon = float(toponym_longitude)
            obj_lat = float(toponym_latitude)

            toponym_name = toponym["metaDataProperty"]["GeocoderMetaData"]["text"]
            if self.show_postal_code:
                postal_code = toponym["metaDataProperty"]["GeocoderMetaData"]["Address"].get("postal_code", "")
                if postal_code:
                    toponym_name = f"{postal_code}, {toponym_name}"

            self.points.append((obj_lon, obj_lat))

            if len(self.points) == 1:
                self.ll = [obj_lon, obj_lat]
            else:
                avg_lon = sum(p[0] for p in self.points) / len(self.points)
                avg_lat = sum(p[1] for p in self.points) / len(self.points)
                self.ll = [avg_lon, avg_lat]

            if spn_flag:
                bbox = toponym.get("boundedBy", {}).get("Envelope", {})
                if bbox:
                    lower_corner = bbox.get("lowerCorner", "").split()
                    upper_corner = bbox.get("upperCorner", "").split()
                    if len(lower_corner) == 2 and len(upper_corner) == 2:
                        min_lon = float(lower_corner[0])
                        min_lat = float(lower_corner[1])
                        max_lon = float(upper_corner[0])
                        max_lat = float(upper_corner[1])

                        delta_lon = max_lon - min_lon
                        delta_lat = max_lat - min_lat

                        self.spn[0] = max(delta_lon * 1.2, 0.0001)
                        self.spn[1] = max(delta_lat * 1.2, 0.0001)
                        self.spn[0] = min(self.spn[0], 90.0)
                        self.spn[1] = min(self.spn[1], 90.0)
                    else:
                        self.spn = [0.005, 0.005]
                else:
                    self.spn = [0.005, 0.005]

            self.gui_elements[0].text = str(round(self.ll[0], 6))
            self.gui_elements[1].text = str(round(self.ll[1], 6))
            if spn_flag:
                self.gui_elements[2].text = str(round(self.spn[0], 6))
                self.gui_elements[3].text = str(round(self.spn[1], 6))

            self.update_map()
            self.show_success(f"Найден: {toponym_name}")

        except Exception as e:
            self.show_error(f"Ошибка при поиске: {str(e)}")

    def update_map(self):
        api_server = "https://static-maps.yandex.ru/v1"
        theme = 'light' if self.light_theme else 'dark'

        params = {
            'll': ",".join(map(str, self.ll)),
            'spn': ','.join(map(str, self.spn)),
            'apikey': STATIC_MAPS_API_KEY,
            'theme': theme,
            'size': '600,450',
            'lang': 'ru_RU',
            'maptype': self.map_types[self.current_map_type_index]  # Добавляем тип карты
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
            response = self.session.get(api_server, params=params)
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
        zoom_step = 2.0

        if key == arcade.key.ENTER:
            self.search_object()
            return

        if key == arcade.key.PAGEUP:
            self.spn[0] = max(self.spn[0] / zoom_step, 0.0001)
            self.spn[1] = max(self.spn[1] / zoom_step, 0.0001)
            self.sync_ui_and_update()
        elif key == arcade.key.PAGEDOWN:
            self.spn[0] = min(self.spn[0] * zoom_step, 90.0)
            self.spn[1] = min(self.spn[1] * zoom_step, 90.0)
            self.sync_ui_and_update()

        move_step_lon = self.spn[0] * 0.1
        move_step_lat = self.spn[1] * 0.1
        if key == arcade.key.UP:
            new_lat = self.ll[1] + move_step_lat
            if new_lat <= MAX_LAT:
                self.ll[1] = new_lat
            else:
                self.show_error("Достигнута северная граница")
        elif key == arcade.key.DOWN:
            new_lat = self.ll[1] - move_step_lat
            if new_lat >= MIN_LAT:
                self.ll[1] = new_lat
            else:
                self.show_error("Достигнута южная граница")
        elif key == arcade.key.LEFT:
            new_lon = self.ll[0] - move_step_lon
            if new_lon >= MIN_LON:
                self.ll[0] = new_lon
            else:
                self.show_error("Достигнута западная граница")
        elif key == arcade.key.RIGHT:
            new_lon = self.ll[0] + move_step_lon
            if new_lon <= MAX_LON:
                self.ll[0] = new_lon
            else:
                self.show_error("Достигнута восточная граница")
        else:
            return

        self.gui_elements[0].text = str(self.ll[0])
        self.gui_elements[1].text = str(self.ll[1])
        self.update_map()

    def sync_ui_and_update(self):
        self.gui_elements[2].text = str(round(self.spn[0], 6))
        self.gui_elements[3].text = str(round(self.spn[1], 6))
        self.update_map()

    def change_theme(self):
        self.light_theme = not self.light_theme
        self.update_map()

    def get_map_bounds(self):
        center_x = SCREEN_WIDTH - MAP_SIZE[0] * MAP_SCALE / 2 - MAP_BORDER
        center_y = SCREEN_HEIGHT / 2
        half_w = MAP_SIZE[0] * MAP_SCALE / 2
        half_h = MAP_SIZE[1] * MAP_SCALE / 2
        left = center_x - half_w
        right = center_x + half_w
        bottom = center_y - half_h
        top = center_y + half_h
        return left, right, bottom, top

    def on_mouse_press(self, x, y, button, modifiers):
        map_left, map_right, map_bottom, map_top = self.get_map_bounds()

        if not (map_left <= x <= map_right and map_bottom <= y <= map_top):
            return

        norm_x = (x - map_left) / (map_right - map_left)
        norm_y = (y - map_bottom) / (map_top - map_bottom)
        geo_lon = (self.ll[0] - self.spn[0] / 2) + norm_x * self.spn[0]
        geo_lat = (self.ll[1] - self.spn[1] / 2) + norm_y * self.spn[1]

        print(f"Клик: экран=({x},{y}) -> geo=({geo_lon:.6f}, {geo_lat:.6f})")

        if button == arcade.MOUSE_BUTTON_LEFT:
            self.search_by_coordinates(geo_lon, geo_lat)
        elif button == arcade.MOUSE_BUTTON_RIGHT:
            self.search_organization(geo_lon, geo_lat)

    def search_by_coordinates(self, lon, lat):
        self.clear_points()

        geocoder_api_server = "http://geocode-maps.yandex.ru/1.x/"
        geocoder_params = {
            "apikey": GEOCODER_API_KEY,
            "geocode": f"{lon},{lat}",
            "format": "json",
            "results": "1",
        }

        try:
            response = requests.get(geocoder_api_server, params=geocoder_params)
            if not response:
                self.show_error("Ошибка при поиске объекта")
                return

            json_response = response.json()
            feature_member = json_response["response"]["GeoObjectCollection"]["featureMember"]

            if not feature_member:
                self.show_error("Объект не найден в данной точке")
                return

            toponym = feature_member[0]["GeoObject"]

            toponym_coordinates = toponym["Point"]["pos"]
            toponym_longitude, toponym_latitude = toponym_coordinates.split(" ")
            obj_lon = float(toponym_longitude)
            obj_lat = float(toponym_latitude)

            toponym_name = toponym["metaDataProperty"]["GeocoderMetaData"]["text"]

            if self.show_postal_code:
                postal_code = toponym["metaDataProperty"]["GeocoderMetaData"]["Address"].get("postal_code", "")
                if postal_code:
                    toponym_name = f"{postal_code}, {toponym_name}"

            self.points.append((obj_lon, obj_lat))

            # Обновляем карту (НЕ меняем ll и spn)
            self.update_map()

            self.show_success(f"Найден: {toponym_name}")

        except Exception as e:
            self.show_error(f"Ошибка при поиске: {str(e)}")

    def search_organization(self, lon, lat):
        self.clear_points()

        search_api_server = "https://search-maps.yandex.ru/v1/"

        search_queries = ["магазин", "кафе", "аптека", "офис", "салон", "банк", "ресторан"]

        closest_org = None
        min_distance = float('inf')

        for query in search_queries:
            search_params = {
                "apikey": SEARCH_API_KEY,
                "text": query,
                "lang": "ru_RU",
                "ll": f"{lon},{lat}",
                "type": "biz",
                "results": "1"
            }

            try:
                response = requests.get(search_api_server, params=search_params)
                if not response:
                    continue

                json_response = response.json()
                features = json_response.get("features", [])

                for feature in features:
                    org_coords = feature["geometry"]["coordinates"]
                    org_lon, org_lat = org_coords[0], org_coords[1]
                    distance = self.hav_distance(lon, lat, org_lon, org_lat)

                    if distance <= 50 and distance < min_distance:
                        min_distance = distance
                        company_data = feature["properties"]["CompanyMetaData"]
                        closest_org = {
                            "name": company_data["name"],
                            "address": company_data["address"],
                            "lon": org_lon,
                            "lat": org_lat,
                            "distance": distance,
                            "category": query
                        }
            except Exception as e:
                print(f"Ошибка при поиске '{query}': {e}")
                continue

        if not closest_org:
            self.show_error("Организации не найдены в радиусе 50 метров")
            return

        org_lon = closest_org["lon"]
        org_lat = closest_org["lat"]

        self.points.append((org_lon, org_lat))

        self.update_map()

        self.show_success(
            f"{closest_org['name']}, {closest_org['address']}"
        )

    @staticmethod
    def hav_distance(lon1, lat1, lon2, lat2):
        R = 6371000  # радиус Земли в м
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)

        a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c


if __name__ == "__main__":
    game = MyGUIWindow()
    arcade.run()
