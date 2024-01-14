#!/usr/bin/env python
""" Contiene la clase que define
el widget de visualización de datos,
ya sea en forma de graficos o en una
QTable
"""
import os
import json
import asyncio
from pathlib import Path
import websockets
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QFrame
from PyQt5.QtWidgets import QGroupBox
from PyQt5.QtWidgets import QTabWidget
from PyQt5.QtWidgets import QTableWidget
from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWidgets import QSizePolicy
#from PyQt5.QtWebEngineWidgets import QWebEngineView

from PyQt5.QtCore import Qt

#import plotly.graph_objs as go
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.dates as mdates
import pandas as pd

from qfluentwidgets import ComboBox
from qfluentwidgets import PrimaryPushButton
from qfluentwidgets import PushButton
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import TeachingTip
from qfluentwidgets import InfoBarIcon
from qfluentwidgets import TeachingTipTailPosition
from qfluentwidgets import TitleLabel
from qfluentwidgets import SubtitleLabel
from qfluentwidgets import BodyLabel
from qfluentwidgets import ToolTipFilter
from qfluentwidgets import ToolTipPosition
from qfluentwidgets import InfoBar
from qfluentwidgets import InfoBarPosition
from qfluentwidgets import FlowLayout
from qfluentwidgets import SmoothScrollArea
from qfluentwidgets import TableWidget
from qfluentwidgets import Slider

#from qframelesswindow.webengine import FramelessWebEngineView

__author__ = "Dario Fervenza"
__copyright__ = "Copyright 2023, DINAK"
__credits__ = ["Dario Fervenza"]

__version__ = "0.2.0"
__maintainer__ = "Dario Fervenza"
__email__ = "dariofg_@hotmail.com"
__status__ = "Development"


BASE_DIR = os.getcwd()
IMAGES_FOLDER = os.path.join(BASE_DIR, "images")
LOGO = os.path.join(IMAGES_FOLDER, "logo.png")
HOME = os.path.join(IMAGES_FOLDER, "home.png")
GRAPH = os.path.join(IMAGES_FOLDER, "graph.png")
ALERTS = os.path.join(IMAGES_FOLDER, "alerts.png")
ANALYTICS = os.path.join(IMAGES_FOLDER, "analytics.png")
STYLE = Path("style/style.qss").read_text()

class GraficosWidget(QFrame):
    """ Crea el widget de graficos
    En el se muestran los datos de la API usando
    un chart de plotly y una Qtable
    """
    def __init__(self):
        super().__init__()
        self.token = None
        self.db_data = None
        self.server_ip = "localhost"
        self.setObjectName("GraficosWidget")
        self.lista_ciudades = ["Vigo", "Lugo", "Madrid"]
        self.lista_variables = ["Temperatura", "Humedad", "Presion"]

        self.df_actual = pd.DataFrame()
        #self.fig = go.Figure()

        tab_maestra = QTabWidget()
        scroll_area_maestra_graficos = SmoothScrollArea()
        tab_graficos_container = QWidget()
        scroll_area_maestra_graficos.setWidget(tab_graficos_container)
        scroll_area_maestra_graficos.setWidgetResizable(True)
        tab_graficos_container.wheelEvent = lambda event: self.on_whell_event(event, scroll_area_maestra_graficos) 
        layout_scroll_maestro_graficos = QVBoxLayout()
        layout_scroll_maestro_graficos.addWidget(tab_graficos_container)
        scroll_area_maestra_graficos.setLayout(layout_scroll_maestro_graficos)

        tab_maestra.addTab(scroll_area_maestra_graficos, "Graficos")

        tab_datos_container = QWidget()
        tab_maestra.addTab(tab_datos_container, "Datos")

        layout_maestro = QVBoxLayout()


        titulo_graficos = TitleLabel("Visualización de los gráficos")
        grupo_anadir_eliminar_graficos = QGroupBox("Modificar datos mostrados")
        layout_grupo_anadir_graf = QGridLayout()
        grupo_anadir_eliminar_graficos.setLayout(layout_grupo_anadir_graf)
        label_anadir_grafico = BodyLabel("Añadir gráfico")
        self.ciudad_anadir_grafico = ComboBox()
        for ciudad in self.lista_ciudades:
            self.ciudad_anadir_grafico.addItem(ciudad)
        self.variable_anadir_grafico = ComboBox()
        for variable in self.lista_variables:
            self.variable_anadir_grafico.addItem(variable)
        boton_anadir_grafico = PushButton(FIF.ADD, "Añadir gráfico", self)
        boton_anadir_grafico.clicked.connect(self.anadir_grafico_func)
        layout_grupo_anadir_graf.addWidget(label_anadir_grafico, 0, 0)   
        layout_grupo_anadir_graf.addWidget(self.ciudad_anadir_grafico, 1, 0)   
        layout_grupo_anadir_graf.addWidget(self.variable_anadir_grafico, 2, 0)   
        layout_grupo_anadir_graf.addWidget(boton_anadir_grafico, 3, 0)

        boton_recargar_datos_de_la_db = PrimaryPushButton(FIF.DOWNLOAD, "Leer datos de la db", self)
        boton_recargar_datos_de_la_db.clicked.connect(self.read_data_from_db)

        boton_recargar_datos_de_la_db.setToolTip("Lee los datos almacenados en la base de datos")
        boton_recargar_datos_de_la_db.installEventFilter(ToolTipFilter(boton_recargar_datos_de_la_db, 300, ToolTipPosition.BOTTOM))
        layout_grupo_anadir_graf.addWidget(boton_recargar_datos_de_la_db, 1, 1, 2, 1)

        label_eliminar_grafico = BodyLabel("Eliminar grupo")
        combobox_grupos_a_eliminar = ComboBox()




        graficos_widget_container = QWidget()
        self.flow_layout_graficos_widget = FlowLayout()
        graficos_widget_container.setLayout(self.flow_layout_graficos_widget)

        self.lista_grupos_graficos = []

        grupo_1 = QGroupBox("Grafico 1: Temperaturas en Vigo")
        canvas_fig_1 = FigureCanvas()
        layout = QVBoxLayout()
        layout.addWidget(canvas_fig_1)
        grupo_1.setLayout(layout)
        self.lista_grupos_graficos.append(grupo_1)

        grupo_2 = QGroupBox("Gráfico 2: Humedad en Vigo")
        canvas_fig_humedad = FigureCanvas()
        layout_humedad = QVBoxLayout()
        layout_humedad.addWidget(canvas_fig_humedad)
        grupo_2.setLayout(layout_humedad)
        self.lista_grupos_graficos.append(grupo_2)

        grupo_3 = QGroupBox("Gráfico 3: Presion en Vigo")
        canvas_fig_3 = FigureCanvas()
        layout_presion = QVBoxLayout()
        layout_presion.addWidget(canvas_fig_3)
        grupo_3.setLayout(layout_presion)
        self.lista_grupos_graficos.append(grupo_3)

        for grupo in self.lista_grupos_graficos:
            self.flow_layout_graficos_widget.addWidget(grupo)

        

        label_eliminar_grafico = BodyLabel("Eliminar grupo")
        self.combobox_grupos_a_eliminar = ComboBox()
        for group in self.lista_grupos_graficos:
            self.combobox_grupos_a_eliminar.addItem(group.title())
        self.boton_eliminar_grafico = PushButton(FIF.DELETE, "Eliminar", self)
        self.boton_eliminar_grafico.clicked.connect(self.eliminar_grafico)
        layout_grupo_anadir_graf.addWidget(label_eliminar_grafico, 0, 2)
        layout_grupo_anadir_graf.addWidget(self.combobox_grupos_a_eliminar, 2, 2)
        layout_grupo_anadir_graf.addWidget(self.boton_eliminar_grafico, 3, 2)

        self.widget_inferior_graphs = QWidget()
        layout_widget_inferior_graphs = QGridLayout()
        self.widget_inferior_graphs.setLayout(layout_widget_inferior_graphs)

        self.explicacion_boton = PushButton(FIF.EDUCATION, "Mostrar explicación", self)
        self.explicacion_boton.clicked.connect(self.mostrar_explicacion_datos)

        subtitulo_cambiar_datos = SubtitleLabel("Modificar tamaño")

        self.grafico_combobox = ComboBox()

        for group in self.lista_grupos_graficos:
            self.grafico_combobox.addItem(group.title())
        self.grafico_combobox.currentIndexChanged.connect(self.modify_graph_target_to_resize)

        self.slider_width = Slider(Qt.Vertical)
        self.slider_width.setValue(75)
        self.slider_width.sliderReleased.connect(self.modify_graph_size)
        self.slider_height = Slider(Qt.Vertical)
        self.slider_height.setValue(75)
        self.slider_height.sliderReleased.connect(self.modify_graph_size)

        layout_widget_inferior_graphs.addWidget(self.explicacion_boton, 0, 0, 1, 3, Qt.AlignmentFlag.AlignTop)
        layout_widget_inferior_graphs.addWidget(subtitulo_cambiar_datos, 1, 0, 1, 3, Qt.AlignmentFlag.AlignTop)
        layout_widget_inferior_graphs.addWidget(self.grafico_combobox, 2, 0, Qt.AlignmentFlag.AlignTop)
        layout_widget_inferior_graphs.addWidget(self.slider_width, 2, 1, Qt.AlignmentFlag.AlignTop)
        layout_widget_inferior_graphs.addWidget(self.slider_height, 2, 2, Qt.AlignmentFlag.AlignTop)
        self.flow_layout_graficos_widget.addWidget(self.widget_inferior_graphs)


        layout_tab_graficos = QGridLayout()
        layout_tab_graficos.addWidget(
            titulo_graficos,
            0,
            0,
            1,
            3,
            Qt.AlignmentFlag.AlignCenter
            )
        layout_tab_graficos.addWidget(
            grupo_anadir_eliminar_graficos,
            1,
            0,
            1,
            3,
            Qt.AlignmentFlag.AlignCenter
            )        
        layout_tab_graficos.addWidget(
            graficos_widget_container,
            2,
            0,
            1,
            3,
            Qt.AlignmentFlag.AlignTop
            )


        layout_tab_graficos.setContentsMargins(10, 30, 10, 10)
        layout_tab_graficos.setRowStretch(8, 1)

        titulo_datos = TitleLabel("Visualización de los datos")
        self.tabla_datos = TableWidget(self)
        self.tabla_datos.setBorderVisible(True)
        self.tabla_datos.setBorderRadius(8)
        self.tabla_datos.setWordWrap(False)
        self.tabla_datos.setRowCount(0)
        self.tabla_datos.setColumnCount(5) 
        self.tabla_datos.verticalHeader().hide()   
        
  
        encabezado = ["Ciudad", "Fecha", "Temperatura", "Humedad", "Presión"]
        #self.tabla_datos.setColumnWidth(1, 150)
        self.tabla_datos.setHorizontalHeaderLabels(encabezado)
        self.boton_actualizar_datos = PushButton(FIF.EDIT, "Recargar datos", self)
        self.boton_actualizar_datos.clicked.connect(self.add_lines_to_data_table)
        self.boton_actualizar_datos.setToolTip("Recarga la tabla de datos")
        self.boton_actualizar_datos.installEventFilter(
            ToolTipFilter(self.boton_actualizar_datos, 0, ToolTipPosition.TOP)
            )

        layout_ver_datos = QVBoxLayout()
        layout_ver_datos.addWidget(titulo_datos)
        layout_ver_datos.addSpacing(15)
        layout_ver_datos.addWidget(self.tabla_datos)
        layout_ver_datos.addWidget(self.boton_actualizar_datos)
        tab_datos_container.setLayout(layout_ver_datos)

        tab_graficos_container.setLayout(layout_tab_graficos)
        layout_maestro.addWidget(tab_maestra)
        self.setLayout(layout_maestro)
        self.read_data_from_db()
        self.create_initial_figures()
        self.add_lines_to_data_table()
    def on_whell_event(self, event, scroll_area):
        delta = event.angleDelta().y()
        delta = int(scroll_area.verticalScrollBar().value() - delta / 3)
        scroll_area.verticalScrollBar().setValue(delta)
    def add_lines_to_data_table_success(self):
        InfoBar.success(
            title='Finalizado',
            content="Datos recargados",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            # position='Custom',   # NOTE: use custom info bar manager
            duration=1000,
            parent=self
        )
    def add_lines_to_data_table(self):
        """ Función encargada de solicitar los
        datos de la API y mostralos en la QTable
        """
        self.tabla_datos.setRowCount(0)
        self.boton_actualizar_datos.setEnabled(False)
        df_maestro = pd.DataFrame()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.retrieve_data_from_db())
        self.create_df_from_data()
        df = self.df_actual
        df_maestro = pd.concat([df_maestro, df])
        df_maestro = df_maestro.sort_values(by=["ciudad", "fecha"], ascending=False)
        for _, row in df_maestro.iterrows():
            lineas_actuales = self.tabla_datos.rowCount()
            self.tabla_datos.setRowCount(lineas_actuales + 1)
            ciudad = row["ciudad"]
            fecha = row["fecha"]
            fecha = fecha.strftime("%Y-%m-%d %H:%M:%S")
            temperatura = str(row["temperatura"])
            humedad = str(row["humedad"])
            presion = str(row["presion"])
            tupla_datos = (ciudad, fecha, temperatura, humedad, presion)
            for i, el in enumerate(tupla_datos):
                element = QTableWidgetItem(el)
                self.tabla_datos.setItem(lineas_actuales, i, element)
        self.tabla_datos.resizeColumnsToContents()
        self.add_lines_to_data_table_success()
        self.boton_actualizar_datos.setEnabled(True)
    def modify_graph_target_to_resize(self):
        grupo_objetivo = self.grafico_combobox.currentText()
        for group in self.lista_grupos_graficos:
            if group.title() == grupo_objetivo:
                width = group.width()
                height = group.height()
                valor_slider_width = 100 - int((width - 250) * 100 / 1000)
                valor_slider_height = 100 - int((height - 250) * 100 / 1000)
                self.slider_width.setValue(valor_slider_width)
                self.slider_height.setValue(valor_slider_height)

    def modify_graph_size(self):
        grafico = self.grafico_combobox.currentText()
        grafico = int(grafico.split(":")[0][-1]) - 1
        width = int((100 - self.slider_width.value())*1000 / 100 + 250)
        height = int((100 - self.slider_height.value())*1000 / 100 + 250)
        group = self.lista_grupos_graficos[grafico]
        canvas = group.layout().itemAt(0).widget()
        canvas.setFixedHeight(height)
        group.setFixedHeight(height)
        canvas.setFixedWidth(width)
        group.setFixedWidth(width)
        canvas.draw()

    def anadir_grafico_func(self):
        width = int((100 - self.slider_width.value())*1000 / 100 + 250)
        height = int((100 - self.slider_height.value())*1000 / 100 + 250)
        ciudad = self.ciudad_anadir_grafico.currentText()
        variable = self.variable_anadir_grafico.currentText()
        fig = self.create_figure(ciudad, variable)
        ultima_figura_index = len(self.lista_grupos_graficos) + 1
        grupo = QGroupBox(f"Gráfico {ultima_figura_index}: {variable} en {ciudad}")
        layout_grupo = QVBoxLayout()
        canvas = FigureCanvas(fig)
        canvas.setFixedHeight(height)
        grupo.setFixedHeight(height)
        canvas.setFixedWidth(width)
        grupo.setFixedWidth(width)
        layout_grupo.addWidget(canvas)
        grupo.setLayout(layout_grupo)
        self.lista_grupos_graficos.append(grupo)
        self.renombrar_grupos()

        self.combobox_grupos_a_eliminar.clear()
        for group in self.lista_grupos_graficos:
            self.combobox_grupos_a_eliminar.addItem(group.title())
        self.grafico_combobox.clear()    
        for group in self.lista_grupos_graficos:
            self.grafico_combobox.addItem(group.title())
        self.volver_a_desplegar_graficos()
    def volver_a_desplegar_graficos(self):
        self.flow_layout_graficos_widget.removeAllWidgets()
        for group in self.lista_grupos_graficos:
            self.flow_layout_graficos_widget.addWidget(group)
        self.flow_layout_graficos_widget.addWidget(self.widget_inferior_graphs)

    def eliminar_grafico(self):
        width = int((100 - self.slider_width.value())*1000 / 100 + 250)
        height = int((100 - self.slider_height.value())*1000 / 100 + 250)
        titulo_grupo = self.combobox_grupos_a_eliminar.currentText()
        for index, group in enumerate(self.lista_grupos_graficos):
            if len(self.lista_grupos_graficos) == 1:
                TeachingTip.create(
                    target=self.boton_eliminar_grafico,
                    icon=InfoBarIcon.ERROR,
                    title="Info",
                    content="No puede eliminarse el último grafico",
                    isClosable=True,
                    tailPosition=TeachingTipTailPosition.BOTTOM,
                    duration=2000,
                    parent=self
                    )
            else:
                if group.title() == titulo_grupo:
                    canvas = group.layout().itemAt(0).widget()
                    canvas.figure.clear()
                    plt.close(canvas.figure)
                    grupo = self.lista_grupos_graficos[index]
                    self.flow_layout_graficos_widget.removeWidget(grupo)
                    grupo.deleteLater()
                    self.lista_grupos_graficos.pop(index)
                    self.renombrar_grupos()
        self.combobox_grupos_a_eliminar.clear()
        for group in self.lista_grupos_graficos:
            self.combobox_grupos_a_eliminar.addItem(group.title())
        self.grafico_combobox.clear()    
        for group in self.lista_grupos_graficos:
            self.grafico_combobox.addItem(group.title())
        self.volver_a_desplegar_graficos()

    def renombrar_grupos(self):
        new_list = []
        for index, group in enumerate(self.lista_grupos_graficos):
            partes_titulo = group.title().split(":")
            parte1 = partes_titulo[0][: -1]
            parte1 = parte1 + str(index + 1) + ":"
            new_title = parte1 + partes_titulo[1]
            group.setTitle(new_title)
            new_list.append(group)
        self.lista_grupos_graficos = new_list

    def read_data_from_db(self):
        """ Llama a la funcion encargada de
        obtener los datos de la db, luego a la
        que genera un DataFrame de pandas y
        por ultimo a la funcion de generar la plotly fig
        """
        self.obtain_data()
        self.create_df_from_data()
        self.add_lines_to_data_table_success()
    def create_initial_figures(self):
        ciudad = self.ciudad_anadir_grafico.currentText()
        width = int((100 - self.slider_width.value())*1000 / 100 + 250)
        height = int((100 - self.slider_height.value())*1000 / 100 + 250)
        fig_tuple = (
            self.create_figure(ciudad, valor="Temperatura"),
            self.create_figure(ciudad, valor="Humedad"),
            self.create_figure(ciudad, valor="Presion")
            )
        for index, group in enumerate(self.lista_grupos_graficos):
            canvas = group.layout().itemAt(0).widget()
            canvas.figure = fig_tuple[index]
            canvas.setFixedHeight(height)
            group.setFixedHeight(height)
            canvas.setFixedWidth(width)
            group.setFixedWidth(width)
            canvas.draw()

    def obtain_data(self):
        """ Lee la ciudad seleccionada en la combobox
        de la tab de visualizar graficos
        y obtiene los datos de la db asociados a esa ciudad
        """
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.retrieve_data_from_db())
    async def retrieve_data_from_db(self):
        """ Realiza la solicitud de datos al servidor
        utilizando websockets
        """
        uri = f"ws://{self.server_ip}:8765"
        query = {}
        token = {"token" : self.token, "query" : query}
        request = {"tipo_request" : "data_request", "value" : token}
        request = json.dumps(request)
        async with websockets.connect(uri) as websocket:
            await websocket.send(request)
            response = await websocket.recv()
            self.db_data = response
            await websocket.close()
    def create_df_from_data(self):
        """ Crea un DataFrame de pandas con los datos
        obtenidos en la funcion read_data_from_db
        Las columnas seleccionadas son la temperatura,
        la presion y la humedad.
        """
        lista_fechas = []
        lista_temperaturas = []
        lista_humedades = []
        lista_presiones = []
        lista_ciudades = []
        datos = json.loads(self.db_data)
        for element in datos:
            try:
                fecha = element["location"]["localtime"]
                temperatura = element["current"]["temperature"]
                humedad = element["current"]["humidity"]
                presion = element["current"]["pressure"]
                ciudad = element["location"]["name"]
                lista_fechas.append(fecha)
                lista_temperaturas.append(temperatura)
                lista_humedades.append(humedad)
                lista_presiones.append(presion)
                lista_ciudades.append(ciudad)
            except KeyError:
                pass
        dict_data = {
            "fecha" : lista_fechas,
            "temperatura" : lista_temperaturas,
            "humedad" : lista_humedades,
            "presion" : lista_presiones,
            "ciudad" : lista_ciudades,
            }
        df = pd.DataFrame(dict_data)
        df["fecha"] = pd.to_datetime(df["fecha"])
        self.df_actual = df
    def create_figure(self, ciudad: str, valor: str):
        datos = self.df_actual
        datos = datos.loc[datos["ciudad"] == ciudad]
        if valor == "Temperatura":
            valor2 = "temperatura"
        elif valor == "Humedad":
            valor2 = "humedad"
        elif valor == "Presion":
            valor2 = "presion"
        fig, ax = plt.subplots(figsize=(5, 6))
        datos = datos[["fecha", valor2]]
        datos = datos.set_index("fecha")
        datos.plot(ax=ax, label=f"{valor} en {ciudad}")
        ax.set_title(f"Evolución {valor2}", fontsize=15)
        ax.set_xlabel("Fecha", fontsize=15)
        ax.set_ylabel(f"{valor}", fontsize=15)
        locator = mdates.WeekdayLocator(interval=2) # Set to every 2 weeks (15 days)
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        fig.tight_layout()
        plt.xticks(rotation=5)
        ax.tick_params(axis='both', which='both', labelsize=12)
        return fig
    """def create_plotly_fig(self, ciudad: str, valor: str, variable: FramelessWebEngineView):"""
    """ Crea una figura de plotly con el DataFrame
    de pandas generado con el metodo create_df_from_data
    y devuelve asigna su html a un widget QWebView, el
    cual es recibido como parametro
    """
    """datos = self.df_actual
    if valor == "Temperatura":
        valor2 = "temperatura"
    elif valor == "Humedad":
        valor2 = "humedad"
    elif valor == "Presion":
        valor2 = "presion"
    self.fig = go.Figure()
    self.fig.add_trace(go.Scatter(
        x=datos["fecha"],
        y=datos[valor2],
        mode="lines",
        name="Temperaturas"
        ))
    self.fig.update_layout(
        title=valor + " en: " + ciudad
        )
    html = self.fig.to_html(include_plotlyjs='cdn')
    variable.setHtml(html)
    print("ok")"""
    def mostrar_explicacion_datos(self):
        content = """
            Los anteriores graficos muestran los datos
            obtenidos de la API de WeatherStack.
            \nSe muestra la temperatura, humedad y presión en
            un de las ciudades (Vigo, Lugo o Madrid).
            \nEn una futura actualización se podrán añadir/eliminar
            gráficos, por ejemplo, si solo quiero ver los gráficos
            de humedad y velocidad del viento (además de combinar ciudades)
            """
        TeachingTip.create(
            target=self.explicacion_boton,
            icon=InfoBarIcon.SUCCESS,
            title="Info",
            content=content,
            isClosable=True,
            tailPosition=TeachingTipTailPosition.TOP,
            duration=20000,
            parent=self
            )