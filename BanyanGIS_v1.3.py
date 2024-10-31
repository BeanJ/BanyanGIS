# -*- coding: utf-8 -*-
"""
Edited on 2024/10/31
@author: Jiaxing Dou (jiaxingdou@mail.bnu.edu.cn)
@coauthor: Yiran Tan (202311079938@mail.bnu.edu.cn)
"""

# Import libraries
import logging
import ctypes
import sys
import geopandas as gpd
import matplotlib.pyplot as plt
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QAction,
    QLabel,
    QFileDialog,
    QMessageBox,
    QVBoxLayout,
    QWidget,
    QInputDialog,
    QDialog,
    QTextEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QSizePolicy,
)
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
)
from matplotlib.backends.backend_qt5agg import (
    NavigationToolbar2QT as NavigationToolbar,
)

ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
    "bnu.banyangis.v1.3"
)

# Set the Chinese font to SimHei
plt.rcParams["font.sans-serif"] = ["SimHei"]  # SimHei font
# Fix for displaying minus signs in axes
plt.rcParams["axes.unicode_minus"] = False


# Logging setup
logging.basicConfig(
    filename="app.log",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def handle_exception(e):
    logging.error(f"Exception occurred: {str(e)}", exc_info=True)
    QMessageBox.critical(
        self.main_window, "Error", f"Failed to display labels: {e}"
    )

    try:
        # Initial call to set label visibility
        update_label_visibility(None)

        # Update the canvas
        self.main_window.canvas.draw()
    except Exception as e:
        handle_exception(e)


# File import class


class ImportFile:
    def import_shapefile(self, parent):
        """Opens a file dialog, reads a shapefile, and returns a GeoDataFrame."""
        file_dialog = QFileDialog(parent)
        file_path, _ = file_dialog.getOpenFileName(
            parent, "Import Shapefile", "", "Shapefiles (*.shp *.geojson)"
        )

        if file_path:
            try:
                # Read the file and return the GeoDataFrame
                gdf = gpd.read_file(file_path)
                return gdf, file_path
            except IOError:
                QMessageBox.critical(
                    parent, "Error", "Error reading the file."
                )
            except Exception as e:
                # Catch any other unexpected errors
                QMessageBox.critical(
                    parent, "Error", f"An unexpected error occurred: {e}"
                )

        return None, None


# Operations class to handle GIS data functionalities
class Operations:
    def __init__(self, main_window):
        self.main_window = main_window
        # self.gdf = None  # The currently opened GeoDataFrame

    def open_file(self):
        gdf, file_path = self.main_window.importer.import_shapefile(
            self.main_window
        )
        if gdf is not None:
            self.main_window.gdf = gdf
            self.main_window.welcome_label.setText(f"Opened file: {file_path}")
            self.display_gis_data()
        else:
            self.main_window.clear_canvas()
        # Update Operations menu state after opening file
        self.main_window.update_operations_menu_state()

    def display_gis_data(self):
        """Displays GIS data on the canvas."""
        if self.main_window.gdf is None:
            QMessageBox.warning(
                self.main_window, "Warning", "No GIS file is opened."
            )
            return
        try:
            self.main_window.figure.clear()  # Clear the figure
            ax = self.main_window.figure.add_subplot(
                111
            )  # Create a new subplot
            self.main_window.gdf.plot(ax=ax)
            ax.axis("on")
            ax.set_xlim(
                self.main_window.gdf.total_bounds[0],
                self.main_window.gdf.total_bounds[2],
            )
            ax.set_ylim(
                self.main_window.gdf.total_bounds[1],
                self.main_window.gdf.total_bounds[3],
            )
            ax.tick_params(axis="x", labelsize=14)
            ax.tick_params(axis="y", labelsize=14)
            self.main_window.canvas.draw()
        except Exception as e:
            QMessageBox.critical(
                self.main_window, "Error", f"Failed to display GIS data: {e}"
            )

    def show_projection_info(self):
        """Displays the projection information."""
        try:
            projection_info = (
                self.main_window.gdf.crs.to_string()
                if self.main_window.gdf.crs
                else "Undefined projection"
            )

            # Create a dialog to display the projection information
            # Use the main window as the parent
            dialog = QDialog(self.main_window)
            dialog.setWindowTitle("Projection Info")

            # Create a text edit widget to display the information
            text_edit = QTextEdit(dialog)
            # Set the projection information
            text_edit.setPlainText(projection_info)
            text_edit.setReadOnly(True)  # Make it read-only

            # Create a layout for the dialog
            layout = QVBoxLayout(dialog)
            layout.addWidget(text_edit)

            # Add a copy button
            copy_button = QPushButton("Copy", dialog)
            copy_button.clicked.connect(
                lambda: self.copy_to_clipboard(text_edit.toPlainText())
            )  # Connect to copy function
            layout.addWidget(copy_button)

            # Add a close button
            close_button = QPushButton("Close", dialog)
            # Close the dialog when button is clicked
            close_button.clicked.connect(dialog.accept)
            layout.addWidget(close_button)

            dialog.setLayout(layout)
            dialog.resize(600, 400)  # Set the initial size of the dialog

            dialog.exec_()  # Show the dialog
        except Exception as e:
            QMessageBox.critical(
                self.main_window,
                "Error",
                f"Failed to get projection info: {e}",
            )

    def copy_to_clipboard(self, text):
        """Copy the text to clipboard."""
        clipboard = QApplication.clipboard()  # Get the clipboard
        clipboard.setText(text)  # Copy the text

    def switch_projection(self):
        """Switch projection based on user input EPSG code."""
        try:
            epsg_code, ok = QInputDialog.getText(
                self.main_window, "Switch Projection", "Enter EPSG code:"
            )
            if not ok or not epsg_code.isdigit():
                QMessageBox.warning(
                    self.main_window, "Warning", "Invalid EPSG code entered."
                )
                return

            epsg_code = int(epsg_code)
            self.main_window.gdf = self.main_window.gdf.to_crs(
                epsg=f"{epsg_code}"
            )
            self.main_window.welcome_label.setText(
                f"Projection switched to EPSG:{epsg_code}"
            )
            self.display_gis_data()
        except Exception as e:
            QMessageBox.warning(
                self.main_window, "Error", f"Failed to switch projection: {e}"
            )

    def clip_data(self):
        """Clip GIS data using another shapefile or raster."""
        if self.main_window.gdf is None:
            QMessageBox.warning(
                self.main_window, "Warning", "No GIS file is opened."
            )
            return

        # Open file dialog to select clip file
        clip_path, _ = QFileDialog.getOpenFileName(
            self.main_window,
            "Select Clip File",
            "",
            "Shapefiles (*.shp);;Raster files (*.tif *.tiff)",
        )

        if not clip_path:
            return

        try:
            # Check file type and perform clipping
            if clip_path.endswith((".shp", ".geojson")):
                clip_gdf = gpd.read_file(clip_path)
                self.main_window.gdf = self.main_window.gdf.clip(clip_gdf)
            elif clip_path.endswith((".tif", ".tiff")):
                import rasterio
                from rasterio.mask import mask

                with rasterio.open(clip_path) as src:
                    bbox = src.bounds
                    self.main_window.gdf = self.main_window.gdf.cx[
                        bbox.left : bbox.right, bbox.bottom : bbox.top
                    ]

            self.display_gis_data()
            QMessageBox.information(
                self.main_window, "Clip Data", "Data clipped successfully."
            )
        except Exception as e:
            QMessageBox.critical(
                self.main_window, "Error", f"Failed to clip data: {e}"
            )

    def show_attribute_table(self):
        """Displays the attribute table of the currently loaded GeoDataFrame in a dialog."""
        if self.main_window.gdf is None:
            QMessageBox.warning(
                self.main_window, "Warning", "No GIS file is opened."
            )
            return

        dialog = QDialog(self.main_window)
        dialog.setWindowTitle("Attribute Table")
        # Add this line to enable maximize button
        dialog.setWindowFlag(Qt.WindowMaximizeButtonHint)
        layout = QVBoxLayout(dialog)

        # Create the table widget to display the attributes
        table = QTableWidget(dialog)
        gdf = self.main_window.gdf

        # Set the table dimensions
        table.setColumnCount(len(gdf.columns))
        table.setRowCount(len(gdf))
        table.setHorizontalHeaderLabels(gdf.columns)

        # Populate the table with GeoDataFrame data
        for i in range(len(gdf)):
            for j, column in enumerate(gdf.columns):
                table.setItem(i, j, QTableWidgetItem(str(gdf.iloc[i, j])))

        layout.addWidget(table)
        close_button = QPushButton("Close", dialog)
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)

        dialog.setLayout(layout)
        dialog.resize(800, 600)
        dialog.exec_()

    def label_features(self):
        """Displays labels for each feature based on a selected field."""
        if self.main_window.gdf is None:
            QMessageBox.warning(
                self.main_window, "Warning", "No GIS file is opened."
            )
            return

        # Get the columns from the attribute table
        columns = self.main_window.gdf.columns.tolist()

        # Prompt the user to select a field for labeling
        field, ok = QInputDialog.getItem(
            self.main_window,
            "Select Field",
            "Choose a field for labeling:",
            columns,
            0,
            False,
        )

        if ok and field:
            try:
                self.main_window.figure.clear()
                ax = self.main_window.figure.add_subplot(111)

                # Plot the geometries
                self.main_window.gdf.plot(ax=ax)

                # Store text labels in a list for later visibility control
                labels = []
                for idx, row in self.main_window.gdf.iterrows():
                    centroid = row["geometry"].centroid
                    label = ax.text(
                        centroid.x,
                        centroid.y,
                        str(row[field]),
                        fontsize=8,
                        ha="center",
                    )
                    labels.append((centroid, label))

                # Define a function to update label visibility based on axis
                # limits
                def update_label_visibility(event):
                    x_min, x_max = ax.get_xlim()
                    y_min, y_max = ax.get_ylim()
                    for centroid, label in labels:
                        # Check if the centroid is within the visible axis
                        # limits
                        visible = (x_min <= centroid.x <= x_max) and (
                            y_min <= centroid.y <= y_max
                        )
                        label.set_visible(visible)

                # Connect the update function to the axes limits change event
                ax.callbacks.connect("xlim_changed", update_label_visibility)
                ax.callbacks.connect("ylim_changed", update_label_visibility)

                # Initial call to set label visibility
                update_label_visibility(None)

                # Update the canvas
                self.main_window.canvas.draw()
            except Exception as e:
                QMessageBox.critical(
                    self.main_window, "Error", f"Failed to display labels: {e}"
                )


# Menu and toolbar manager class
class Menus:
    def __init__(self, main_window):
        self.main_window = main_window
        self.operations = Operations(self.main_window)
        self.create_menus()

    def create_menus(self):
        """Creates menu bar and toolbar for the application."""
        # Menubar
        menubar = self.main_window.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")
        open_action = QAction("Import Shapefile", self.main_window)
        file_menu.addAction(open_action)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.operations.open_file)
        close_action = QAction("Close", self.main_window)
        file_menu.addAction(close_action)
        close_action.triggered.connect(self.main_window.close)

        # Operations menu
        operations_menu = menubar.addMenu("Operations")
        # Get Projection Information action
        self.projection_action = QAction(
            "Get Projection Info", self.main_window
        )
        operations_menu.addAction(self.projection_action)
        self.projection_action.triggered.connect(
            self.operations.show_projection_info
        )
        # Switch Projection action
        self.switch_proj_action = QAction(
            "Switch Projection", self.main_window
        )
        operations_menu.addAction(self.switch_proj_action)
        self.switch_proj_action.triggered.connect(
            self.operations.switch_projection
        )
        # Clip action
        self.clip_action = QAction("Clip", self.main_window)
        operations_menu.addAction(self.clip_action)
        self.clip_action.triggered.connect(self.operations.clip_data)
        # Show Attribute Table action
        self.attr_table_action = QAction(
            "Show Attribute Table", self.main_window
        )
        operations_menu.addAction(self.attr_table_action)
        self.attr_table_action.triggered.connect(
            self.operations.show_attribute_table
        )
        # Show label
        self.label_action = QAction("Label Features", self.main_window)
        operations_menu.addAction(self.label_action)
        self.label_action.triggered.connect(self.operations.label_features)


class CustomNavigationToolbar(NavigationToolbar):
    def __init__(self, canvas, parent, coordinates=True):
        super().__init__(canvas, parent, coordinates)
        self._icon_paths = {
            "Home": r"icons\home.png",
            "Back": r"icons\pfanhui.png",
            "Forward": r"icons\pforward.png",
            "Pan": r"icons\pan.png",
            "Zoom": r"icons\zoom-extent.png",
            "Subplots": r"icons\edit-border.png",
            "Customize": r"icons\edit-text.png",
            "Save": r"icons\save.png",
        }
        self._update_icons()

    def _update_icons(self):
        for action in self.actions():
            if action.text() in self._icon_paths:
                icon_path = self._icon_paths[action.text()]
                action.setIcon(QIcon(icon_path))


# UI MainWindow class


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Initialize ImportFile class
        self.importer = ImportFile()

        # Setup window properties
        self.setWindowTitle("Banyan GIS - v1.3")
        self.setWindowIcon(QIcon(r"icons\banyantree.png"))
        self.setGeometry(100, 100, 800, 600)

        # Initialize central widget
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        self.layout = QVBoxLayout(central_widget)

        # Initialize label
        self.welcome_label = QLabel(
            "Welcome to the preview version of Banyan GIS", self
        )
        self.welcome_label.setAlignment(Qt.AlignCenter)
        self.welcome_label.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed
        )
        self.layout.addWidget(self.welcome_label)

        # Matplotlib Figure and Canvas
        self.figure = plt.Figure(figsize=(10, 8))
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas)

        # Add Navigation Toolbar
        self.toolbar = CustomNavigationToolbar(self.canvas, self)
        self.layout.addWidget(self.toolbar)

        # Initialize Operations class
        self.operations = Operations(self)

        # Initialize menu and toolbar manager
        self.menus = Menus(self)

        # Initial empty state for the canvas
        self.clear_canvas()

        # Update the state of Operations menu
        self.update_operations_menu_state()

    def clear_canvas(self):
        """Clears the canvas at initialization."""
        self.gdf = None  # Reset to no opened file
        self.figure.clear()  # Clear the figure at initialization
        self.canvas.draw()  # Refresh the canvas to show it empty

        # Update Operations menu state after clearing the canvas
        self.update_operations_menu_state()

    def update_operations_menu_state(self):
        """Enable or disable Operations menu items based on whether a file is opened."""
        has_file_opened = self.gdf is not None
        self.menus.attr_table_action.setEnabled(has_file_opened)
        self.menus.projection_action.setEnabled(has_file_opened)
        self.menus.switch_proj_action.setEnabled(has_file_opened)
        self.menus.clip_action.setEnabled(has_file_opened)
        self.menus.label_action.setEnabled(has_file_opened)


# Main function to start the app
if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())
