from qgis.PyQt.QtCore import QCoreApplication


class GuiTranslator:

    @staticmethod
    def tr(context, message):
        return QCoreApplication.instance().translate(context, message)
