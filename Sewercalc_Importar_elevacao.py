from qgis.core import QgsProject, QgsRaster, Qgis, QgsProcessingException
from qgis.utils import iface
from PyQt5.QtCore import QTimer, QVariant
from .Sewercalc_Estilo import aplicar_estilo
from .Sewercalc_Informacoes import verificar_camadas
from .Sewercalc_Add_colunas_funcao import Add_colunas
from .Sewercalc_config_cx_txt import carregar_configuracoes
import json

def importar_elevacao():
    
    #-------------------------------------------------
    camadas_verificar = ["MDE", "PV"]
    nao_encontradas = verificar_camadas(camadas_verificar)
    
    if nao_encontradas:  # Mais pythonico que len() >= 1
        camadas_faltantes = "\n• " + "\n• ".join(nao_encontradas)  # Formato com bullets
        iface.messageBar().pushMessage(
            "Erro: Camadas faltantes", 
            f"As seguintes camadas não foram encontradas:{camadas_faltantes}",
            level=Qgis.Critical, 
            duration=10 
        )
        return
    #-------------------------------------------------
    configuracoes = carregar_configuracoes()
    camada_pv = configuracoes.get("camada_pv") 
    camada_mde = configuracoes.get("camada_mde")
    
    Add_colunas(camada_pv, [("CT", QVariant.Double, 10, 3)])
    
    layer_pv = QgsProject.instance().mapLayer(camada_pv)
    layer_mde = QgsProject.instance().mapLayer(camada_mde)

    if not layer_pv or not layer_mde:
        iface.messageBar().pushMessage(
        "Erro", 
        "Não foi possível carregar as camadas.", 
        level=Qgis.Critical, 
        duration=7)
        return

    # Função para obter a cota do MDE no ponto
    def import_cota_mde(ponto, mde):
        ident = mde.dataProvider().identify(ponto, QgsRaster.IdentifyFormatValue)
        if ident.isValid():
            return ident.results().get(1)  # Índice 1 é o valor da banda 1 (elevação)
        return None

    layer_pv.startEditing()

    # Iterar sobre as feições da camada PV
    for pv in layer_pv.getFeatures():
        ponto = pv.geometry().asPoint()  
        elevacao = import_cota_mde(ponto, layer_mde)  

        if elevacao is not None:
            pv['CT'] = elevacao  
            layer_pv.updateFeature(pv)  

   
    layer_pv.commitChanges()
    aplicar_estilo(camada_pv, "Estilo02_PV.qml")

   
    iface.messageBar().pushMessage(
    "Sucesso",
    "Elevações atribuídas aos PVs com sucesso!",
    level=Qgis.Success,
    duration=7)
