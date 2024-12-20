from kivymd.app import MDApp
from get_data import GetData
class MainApp(MDApp):
    pass

if __name__ == '__main__':
    GetData()
    MainApp().run()