from qgis.PyQt.QtCore import QCoreApplication


class GuiTranslator:

    @staticmethod
    def tr(context):
        return QCoreApplication.instance().translate(context, context)
