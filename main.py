import sys
from site2 import site2
from site3 import carleader
from site1 import site1
from comparaison import recup_article_chrono
from concurrent.futures import ThreadPoolExecutor
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel,
    QComboBox, QPushButton, QTextEdit,QHBoxLayout, QCheckBox, QGroupBox
)
from PySide6.QtCore import QTimer

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Application de relever prix")
        self.setGeometry(100, 100, 400, 300)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f4f4f4;
            }
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #333;
            }
            QGroupBox {
                font-size: 12px;
                font-weight: bold;
                color: #555;
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 10px;
                background-color: #fff;
            }
            QCheckBox {
                font-size: 12px;
                color: #444;
            }
            QPushButton {
                font-size: 14px;
                color: #fff;
                background-color: #007bff;
                border: none;
                border-radius: 5px;
                padding: 8px 12px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QComboBox {
                font-size: 12px;
                color: #333;
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 3px;
                background-color: #fff;
            }
            QGroupBox#frequencyGroupBox {
                margin-top: 10px;
                padding: 10px;
                min-height: 100px;  /* Réduit la hauteur du group */
                max-height: 120px;  /* Limite la hauteur maximale */
            }
        """)
        
        main_layout = QVBoxLayout()
        
        sites = ['IHLE', 'Districash', 'Carleader', 'Chrono']
        self.site_functions = [site1, site2, carleader, recup_article_chrono]
        
        site_layout = QHBoxLayout()
        self.checkboxes = []
        self.buttons = []
        
        for site in sites:
            group_box = QGroupBox(f'{site}')
            group_box.setObjectName(f'{site}GroupBox')
            pair_layout = QVBoxLayout()
            checkbox = QCheckBox('Activer')
            button = QPushButton('Parametres')
            pair_layout.addWidget(checkbox)
            pair_layout.addWidget(button)
            group_box.setLayout(pair_layout)
            site_layout.addWidget(group_box)
            self.checkboxes.append(checkbox)
            self.buttons.append(button)
            
        main_layout.addLayout(site_layout)
            
        group_box = QGroupBox()
        group_box.setObjectName("frequencyGroupBox")
        pair_layout = QVBoxLayout()
        label_instruction = QLabel('Choisissez une fréquence pour exécuter le programme :')
        
        self.combo_frequency = QComboBox()
        self.combo_frequency.addItems([
            'Tous les jours',
            'Toutes les semaines',
            'Une fois tous les 15 jours',
            'Une fois par mois'
        ])
        
        pair_layout.addWidget(label_instruction)
        pair_layout.addWidget(self.combo_frequency)
        
        group_box.setLayout(pair_layout)
        main_layout.addWidget(group_box)
        
        button = QPushButton("Lancer le programme")
        button.clicked.connect(self.schedule_program)
        main_layout.addWidget(button)
        
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.launch_program)
        
    def schedule_program(self):
        """Planifie le lancement périodique en fonction de la fréquence sélectionnée."""
        frequency = self.combo_frequency.currentText()
        interval_ms = 0

        # Calcul des intervalles en millisecondes
        if frequency == 'Tous les jours':
            interval_ms = 24 * 60 * 60 * 1000  # 1 jour en millisecondes
        elif frequency == 'Toutes les semaines':
            interval_ms = 7 * 24 * 60 * 60 * 1000  # 1 semaine en millisecondes
        elif frequency == 'Une fois tous les 15 jours':
            interval_ms = 15 * 24 * 60 * 60 * 1000  # 15 jours en millisecondes
        elif frequency == 'Une fois par mois':
            interval_ms = 30 * 24 * 60 * 60 * 1000  # 30 jours en millisecondes

        # Vérifiez si la fréquence est valide et démarrez le timer
        if interval_ms > 0:
            # Exécution immédiate de la tâche
            self.launch_program()  # Appel immédiat de la fonction pour exécuter la tâche dès maintenant

            # Planification du timer
            self.timer = QTimer(self)  # Créez un QTimer si ce n'est pas déjà fait
            self.timer.setInterval(interval_ms)  # Définir l'intervalle de temps
            self.timer.timeout.connect(self.launch_program)  # Connectez l'événement à la méthode d'exécution
            self.timer.start()  # Démarrez le timer

            print(f"Programme exécuté immédiatement et planifié toutes les {frequency.lower()}.")
        else:
            print("Fréquence invalide")
            
    def launch_program(self):
        """Lance les fonctions activées."""
        with ThreadPoolExecutor() as executor:
            for checkbox, function in zip(self.checkboxes, self.site_functions):
                if checkbox.isChecked():
                    executor.submit(function)
        
if __name__ == '__main__':
    app = QApplication()
    
    widget = MainWindow()
    widget.resize(800,600)
    widget.show()
    
    sys.exit(app.exec())
        
        