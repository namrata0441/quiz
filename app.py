from PyQt5 import QtWidgets
from ui.main import MainWindowUi
from question.Question import QuestionBank
from question.Test import TestBank

"""The application entry point"""


class App:
    @staticmethod
    def setup():
        import sys

        # When first running the application, we set up our QuestionBank and TestBank singletons.
        # By doing this here, we ensure that if we have a question bank and test bank persisted,
        # then they will be loaded into memory straight away.
        QuestionBank.getInstance()
        TestBank.getInstance()

        # set up the ui
        app = QtWidgets.QApplication(sys.argv)
        mainWindow = QtWidgets.QMainWindow()
        ui = MainWindowUi()
        ui.setupUi(mainWindow)
        mainWindow.show()
        sys.exit(app.exec_())


if __name__ == "__main__":
    App.setup()
