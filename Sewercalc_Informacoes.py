from qgis.core import QgsProject,QgsVectorLayer, QgsFeature
from PyQt5.QtCore import QVariant
from qgis.PyQt.QtWidgets import QMessageBox
from .Sewercalc_Add_colunas_funcao import Add_colunas
from .Sewercalc_config_cx_txt import carregar_configuracoes
import json

camada_rede = carregar_configuracoes().get("camada_rede")
camada_pv = carregar_configuracoes().get("camada_pv")
camada_mde = carregar_configuracoes().get("camada_mde")


class parametros:
    def __init__(self):
        config = carregar_configuracoes()
        self.camada_rede = config.get("camada_rede")
        self.camada_pv = config.get("camada_pv") 
        self.camada_mde = config.get("camada_mde")

        self.L = self.comprimento_rede_contribuicao(self.camada_rede) if self.camada_rede else None
        self.LT = self.comprimento_rede_total(self.camada_rede) if self.camada_rede else None
        self.DN_tab= {
            #100: 0.58,
            150: 0.84,
            200: 1.00,
            250: 1.25,
            300: 1.45,
            350: 1.45,
            400: 1.45
        }
        self.DI_tab= {
            #100: 0.58,
            152.8: 0.84,
            191: 1.00,
            237.8: 1.25,
            299.6: 1.45,
            337.6: 1.45,
            380.4: 1.45
        }

    #------------------------------------------------------   
    def comprimento_rede_total(self, camada_rede):
        layer_rede = QgsProject.instance().mapLayer(camada_rede)
        
        if not layer_rede:
            self.msg_box("ERRO!!", "Camada da REDE de esgoto não encontrada!!")
            return 0
        
        provider = layer_rede.dataProvider()
        col_comprimento = 'L'
        
        if col_comprimento not in provider.fields().names():
            self.msg_box("ERRO!!", "A coluna comprimento 'L' não encontrada na camada REDE!!")
            return 0
        
        total_comprimento = 0
        for feature in layer_rede.getFeatures():  # Itera sobre os trechos
            total_comprimento += feature[col_comprimento]
            #print(round(total_comprimento,2))
        return round(total_comprimento,2)
        
     #------------------------------------------------------   
    def comprimento_rede_contribuicao(self, camada_rede):
        layer_rede = QgsProject.instance().mapLayer(camada_rede)
        
        if not layer_rede:
            self.msg_box("ERRO!!", "Camada da REDE de esgoto não encontrada!!")
            return 0
        
        provider = layer_rede.dataProvider()
        col_comprimento = 'L'
        col_contrib = 'CONTRIB'
        
        if col_comprimento not in provider.fields().names():
            self.msg_box("ERRO!!", "A coluna comprimento 'L' não encontrada na camada REDE!!")
            return 0
        
        if col_contrib not in provider.fields().names():
            self.msg_box("ERRO!!", "A coluna de contribuição 'CONTRIB' não encontrada na camada REDE!!")
            return 0
        
        total_comprimento = 0
        for feature in layer_rede.getFeatures():  # Itera sobre os trechos
            if feature[col_contrib] == "SIM":  # Verifica se a contribuição é "SIM"
                total_comprimento += feature[col_comprimento]
        
        return round(total_comprimento, 2)

    #------------------------------------------------------   
    def msg_box(self, title, message):
        msg_box = QMessageBox()
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.exec_()


def obter_db_camada(camada):
    # Acessa a camada pelo nome
    global camada_rede
    global camada_pv
    layer = QgsProject.instance().mapLayer(camada)

    camada_dict = {}

    # Itera sobre todas as feições da camada
    for feicao in layer.getFeatures():
        Atributos_dict = {}

        for coluna in feicao.fields().names():
            Atributos_dict[coluna] = feicao[coluna]
        
        camada_dict[feicao.id()] = Atributos_dict
    ''''
    # Organiza as feições por ordem crescente de 'Calc'
    if camada == camada_rede:
        camada_dict_organizada = dict(sorted(camada_dict.items(), key=lambda item: item[1]['Calc']))
        #print(camada_rede)
        return camada_dict_organizada
    else:
        #print(camada)
        return camada_dict
        '''
        
    return camada_dict
 
def classificar_trechos(tabela_rede, tabela_pv):
   
    N_calc = 1
    Qnt_trechos = len(tabela_rede)

    # Função para encontrar o ID pelo nome
    def encontrar_id(nome_pv):
        for id_pv, dados in tabela_pv.items():
            if dados['NOME'] == nome_pv:
                return id_pv
        return None

    # Adicionar a coluna 'CALC' na camada_rede e classificar PS
    for feicao_id, col in tabela_rede.items():
        PVM = col['PV_MONT']
        id_pv_mont = encontrar_id(PVM)

        col['CALC'] = 0  # Inicializar a coluna CALC

        if tabela_pv[id_pv_mont]['CAT'] == "PS":
            col['CALC'] = N_calc
            Qnt_trechos -= 1

    N_calc += 1

    trechos_calc = {}  # Trechos com montante já classificados
    while Qnt_trechos != 0:
        for feicao_id, col in tabela_rede.items():
            if col['CALC'] == 0:
                trechos_montante = {}
                PVM = col['PV_MONT']

                # Verificar trechos conectados ao montante
                for trecho, coluna in tabela_rede.items():
                    PVJ = coluna['PV_JUS']
                    if PVJ == PVM:
                        trechos_montante[coluna['NOME']] = coluna['CALC']

                # Classificar apenas se todos os montantes já estiverem preenchidos
                if all(valor != 0 for valor in trechos_montante.values()):
                    trechos_calc[feicao_id] = N_calc

        # Atualizar a tabela_rede com os trechos classificados
        for trecho_id, valor_calc in trechos_calc.items():
            tabela_rede[trecho_id]['CALC'] = valor_calc
            N_calc += 1
            Qnt_trechos -= 1
        trechos_calc = {}

        tabela_rede = dict(sorted(tabela_rede.items(), key=lambda item: item[1]['CALC']))
    return tabela_rede

def calcular_comprimento_rede():

    global camada_rede
    layer_rede = QgsProject.instance().mapLayer(camada_rede)
    
    if not layer_rede:
        print(f"A camada '{camada_rede}' não foi encontrada.")
        return
        
    # Verificar se a coluna 'L' existe, se não existir, criar
    if "L" not in layer_rede.fields().names():
        Add_colunas(camada_rede, [("L", QVariant.Double, 10, 2)])
        layer_rede.updateFields() 
        print("Coluna 'L' criada com sucesso.")

    
    idx_coluna_L = layer_rede.fields().indexFromName("L")

    # Iniciar edição da camada
    layer_rede.startEditing()
    
    for feature in layer_rede.getFeatures():
        geom = feature.geometry()
        
        # Verificar se a geometria é válida 
        if geom is None or geom.isEmpty():
            print(f"Feição {feature.id()} tem geometria nula ou vazia. Pulando...")
            continue
        
        if not geom.isGeosValid():
            print(f"Feição {feature.id()} tem geometria inválida. Pulando...")
            continue
        
        comprimento = geom.length()  # Calcula o comprimento da linha
        
        # Evitar valores nulos na coluna
        if comprimento is None:
            comprimento = 0.0

        layer_rede.changeAttributeValue(feature.id(), idx_coluna_L, comprimento)  # Atualiza o atributo
    
    layer_rede.commitChanges()
    '''# Salvar edição
    if layer_rede.commitChanges():
        print("Comprimento dos trechos calculado e armazenado na coluna 'L' com sucesso.")
    else:
        print("Erro ao salvar as alterações na camada 'REDE'.")'''
        
def preencher_contrib_rede():
    
    global camada_rede
    layer_rede = QgsProject.instance().mapLayer(camada_rede)

    if not layer_rede:
        print(f"A camada '{camada_rede}' não foi encontrada.")
        return

    # Verificar se a coluna 'CONTRIB' 
    if "CONTRIB" not in layer_rede.fields().names():
        Add_colunas(camada_rede, [("CONTRIB", QVariant.String, 10)])
        layer_rede.updateFields()
        #print("Coluna 'CONTRIB' criada com sucesso.")

    idx_coluna_contrib = layer_rede.fields().indexFromName("CONTRIB")
    layer_rede.startEditing()

    for feature in layer_rede.getFeatures():
        valor_atual = feature.attribute("CONTRIB")
        if not valor_atual:
            layer_rede.changeAttributeValue(feature.id(), idx_coluna_contrib, "SIM")
    
    layer_rede.commitChanges()
    
    '''if layer_rede.commitChanges():
        print("Valores vazios na coluna 'CONTRIB' foram preenchidos com 'SIM'.")
    else:
        print("Erro ao salvar as alterações na camada 'REDE'.")'''

def verificar_camadas(camadas):
    configuracoes = carregar_configuracoes()
    layer_nao_encontrado = []
    
    for layer in camadas:
        if layer == "PV":
            id_camada_pv= configuracoes.get("camada_pv") 
            camada_pv = QgsProject.instance().mapLayer(id_camada_pv)
            if camada_pv is None:
                layer_nao_encontrado.append(layer)

        elif layer == "REDE":
            id_camada_rede = configuracoes.get("camada_rede")
            camada_rede = QgsProject.instance().mapLayer(id_camada_rede)
            if camada_rede is None:
                layer_nao_encontrado.append(layer)

        elif layer == "MDE":
            id_camada_mde = configuracoes.get("camada_mde") 
            camada_mde = QgsProject.instance().mapLayer(id_camada_mde)
            if camada_mde is None:
                layer_nao_encontrado.append(layer)
    
    return layer_nao_encontrado