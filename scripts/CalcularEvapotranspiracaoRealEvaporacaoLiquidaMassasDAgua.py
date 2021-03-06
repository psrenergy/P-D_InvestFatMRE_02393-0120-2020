#coding: utf-8
'''
Created on November 1, 2021

@author: Andre Granville
'''
# Import libraries
import arcpy, sys, time, os
import traceback
from Util import File 
import Constantes
import arcpy.cartography as CA
from arcpy.sa import *

# mese correspondentes ao perido umido e seco do levantamento de massa dagua em imagens LandSat
meses_periodo_umido = [2,3,4,5]
meses_periodo_seco = [7,8,9,10]
meses_nao_considerados = [1,6,11,12]

def CalcularEvaporacaoLiquidaHistoricaMassasDAgua(shapefileMassaDAguaLandsatAgregado):    
    """
    
    """   
    pymsg = ""
    msgs = ""
    
    try:

        
    except:
        
        # Get the traceback object
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        
        # Concatenate error information into message string
        pymsg = 'PYTHON ERRORS:\nTraceback info:\n{0}\nError Info:\n{1}'\
              .format(tbinfo, str(sys.exc_info()[1]))
        
        msgs = 'ArcPy ERRORS:\n {0}\n'.format(arcpy.GetMessages(2))
      
        # Return python error messages for script tool or Python Window
        arcpy.AddError(pymsg)
        arcpy.AddError(msgs)

    finally:
        
        if len(pymsg)>0 or len(msgs)>0:
            sys.exit(0)
    
    
def CalcularEvaporacaoReferenciaHistoricaMassasDAgua(shapefileMassaDAguaLandsatAgregado):    
    """
    
    """   
    pymsg = ""
    msgs = ""
    
    try:

        definirPontosMargemMassaDagua(shapefileMassaDAguaLandsatAgregado)
        calcularMediaHistoricaEvaporacaoReferenciaPorMassaDagua(Constantes.ARQUIVO_HISTORICO_MASSA_DAGUA_PONTOS_MARGEM_AGREGADO,anoInicialHistorico, anoFinalHistorico)
        
    except:
        
        # Get the traceback object
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        
        # Concatenate error information into message string
        pymsg = 'PYTHON ERRORS:\nTraceback info:\n{0}\nError Info:\n{1}'\
              .format(tbinfo, str(sys.exc_info()[1]))
        
        msgs = 'ArcPy ERRORS:\n {0}\n'.format(arcpy.GetMessages(2))
      
        # Return python error messages for script tool or Python Window
        arcpy.AddError(pymsg)
        arcpy.AddError(msgs)

    finally:
        
        if len(pymsg)>0 or len(msgs)>0:
            sys.exit(0)
    
def definirPontosMargemMassaDagua(shapefileMassaDAguaLandsatAgregado):
    """
    Cria camada de pontos das margens das massas dagua de todo o periodo historico.
    
    """

    pymsg = ""
    msgs = ""
    
    try:
        
        #Simplifica a forma de poligono, de forma a reduzir o numero de vertices 
        #usando a tolerancia minima
        tolerancia = 200
        
        simplifiedEmMEmoria= "in_memory\Simplified"
        CA.SimplifyPolygon(shapefileMassaDAguaLandsatAgregado, simplifiedEmMEmoria, "POINT_REMOVE", tolerancia, "", "#", "NO_KEEP")

        verticesEmMemoria= "in_memory\Vertices"
        arcpy.FeatureVerticesToPoints_management(simplifiedEmMEmoria, verticesEmMemoria, "ALL")

        #Persiste a camada simplificada dos poligonos representando as massas d'??gua
        arcpy.CopyFeatures_management(simplifiedEmMEmoria, Constantes.ARQUIVO_HISTORICO_MASSA_DAGUA_AGREGADO_SIMPLIFY)

        #Persiste a camada, os pontos dos v??rtices dos poligonos simplificados das massas dagua
        arcpy.CopyFeatures_management(verticesEmMemoria, Constantes.ARQUIVO_HISTORICO_MASSA_DAGUA_PONTOS_MARGEM_AGREGADO)

        #libera a memoria utilizada  
        arcpy.Delete_management("in_memory")
        
    
    except:
        
        # Get the traceback object
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        
        # Concatenate error information into message string
        pymsg = 'PYTHON ERRORS:\nTraceback info:\n{0}\nError Info:\n{1}'\
              .format(tbinfo, str(sys.exc_info()[1]))
        
        msgs = 'ArcPy ERRORS:\n {0}\n'.format(arcpy.GetMessages(2))
      
        # Return python error messages for script tool or Python Window
        arcpy.AddError(pymsg)
        arcpy.AddError(msgs)

    finally:
        
        if len(pymsg)>0 or len(msgs)>0:
            sys.exit(0)


def ComputarEvaporacaoReferenciaMediaPorPeriodoDoAno(tabelaHistoricaEvapRefMedia, periodo, mesesDoAno):
    """
    """
    
    #Historico Evapora????o de Refer??ncia Medio
    
    tabelaHistoricaEvapRefMedia_tableview = r"in_memory\tabelaHistoricaEvapRefMedia_tview"
    arcpy.MakeTableView_management(tabelaHistoricaEvapRefMedia, tabelaHistoricaEvapRefMedia_tableview)
    
    sqlWHhere =   Constantes.NOME_ATRIBUTO_MES + ' IN ' + str(tuple(mesesDoAno))  
    arcpy.SelectLayerByAttribute_management (tabelaHistoricaEvapRefMedia_tableview, "NEW_SELECTION", sqlWHhere) 
    
    #Calcula a Evapora????o de Refer??ncia media por Massa DAgua, Ano
    tabelaHistoricaEvapRefMediaSumarizada = "tabela_evapref_{periodo}_sumarizada".format(periodo=periodo)
    nomeAtributoEstatisticaEvapRef = Constantes.NOME_ATRIBUTO_EVAPREF_MEDIO
    estatistica = [[nomeAtributoEstatisticaEvapRef, 'MEAN']]  
    atributoAgregador = "gid;nmoriginal;ano"
    
    arcpy.Statistics_analysis(tabelaHistoricaEvapRefMedia_tableview, tabelaHistoricaEvapRefMediaSumarizada, estatistica, atributoAgregador)
    
    #libera dados em memoria
    arcpy.Delete_management("in_memory")
    
    return tabelaHistoricaEvapRefMediaSumarizada

def populaEvaporacaoReferenciaMediaMesesSemDados(tabelaHistoricaEvapRefMedia, anoInicialHistorico, anoFinalHistorico):
    """
       Preenche os dados de Evapora????o de Refer??ncia m??dia para os meses que n??o est??o dentro do per??odo ??mido e seco (Janeiro, Junho, Novemro e Dezembro) 
       
       Metodologia:
          Computa a Evapora????o de Refer??ncia media referente aos meses umidos e secos.
          Ser?? atribu??do o valor m??dio anual (media umido/m??dio seco) para os meses n??o cobertos pelas esta????es umidas e secas 
       
          Para os anos em que existiram dados referente apenas ao per??odo seco ou ao per??odo ??mido, ser?? atribuido o Evapora????o de Refer??ncia do per??odo existente.
          Para os anos em que n??o existirem dados, por hora, ser?? deixado em branco 

    """    
    tabelaHistoricaEvapRefMediaPeriodoUmidoSumarizada = ComputarEvaporacaoReferenciaMediaPorPeriodoDoAno(tabelaHistoricaEvapRefMedia, 'umido', meses_periodo_umido)
    tabelaHistoricaEvapRefMediaPeriodoSecoSumarizada = ComputarEvaporacaoReferenciaMediaPorPeriodoDoAno(tabelaHistoricaEvapRefMedia, 'seco', meses_periodo_seco)
    
    EvapRefMediaMassaDagua ={}
    nomeMassaDagua={}
    
    EvapRefMediaUmidoMassaDagua ={}
    EvapRefMediaSecoMassaDagua ={}
    nomeMassaDaguaUmido={}
    nomeMassaDaguaSeco={}

    atributosTabelaSumarizada = [Constantes.NOME_ATRIBUTO_ID_MASSA_DAGUA, Constantes.NOME_ATRIBUTO_MASSA_DAGUA, Constantes.NOME_ATRIBUTO_ANO, 'MEAN_' + Constantes.NOME_ATRIBUTO_EVAPREF_MEDIO]
    atributosTabelaHistorica = [Constantes.NOME_ATRIBUTO_ID_MASSA_DAGUA, Constantes.NOME_ATRIBUTO_MASSA_DAGUA, Constantes.NOME_ATRIBUTO_ANO, Constantes.NOME_ATRIBUTO_MES, Constantes.NOME_ATRIBUTO_EVAPREF_MEDIO]
    
    for ano in range(anoInicialHistorico, anoFinalHistorico + 1):
        
        sqlWhere = Constantes.NOME_ATRIBUTO_ANO + " = "  + str(ano)
      
        with arcpy.da.SearchCursor(tabelaHistoricaEvapRefMediaPeriodoUmidoSumarizada, atributosTabelaSumarizada, sqlWhere) as cursor:
            for row in cursor:
                EvapRefMediaUmidoMassaDagua[row[0]] = row[3]
                nomeMassaDaguaUmido[row[0]] = row[1]
                
                
        with arcpy.da.SearchCursor(tabelaHistoricaEvapRefMediaPeriodoSecoSumarizada, atributosTabelaSumarizada, sqlWhere) as cursor:
            for row in cursor:
                EvapRefMediaSecoMassaDagua[row[0]] = row[3]
                nomeMassaDaguaSeco[row[0]] = row[1]
    
        
        if EvapRefMediaUmidoMassaDagua or EvapRefMediaSecoMassaDagua:
        
            if EvapRefMediaUmidoMassaDagua:
                EvapRefMediaMassaDagua = EvapRefMediaUmidoMassaDagua
                nomeMassaDagua = nomeMassaDaguaUmido
               
            if EvapRefMediaSecoMassaDagua:
                EvapRefMediaMassaDagua = EvapRefMediaSecoMassaDagua
                nomeMassaDagua = nomeMassaDaguaSeco
            
            with arcpy.da.InsertCursor(tabelaHistoricaEvapRefMedia, atributosTabelaHistorica) as cursorDestino:
                
                for massaDAguaId in EvapRefMediaMassaDagua:
                    for mes in meses_nao_considerados: 
                        
                        if not EvapRefMediaUmidoMassaDagua:
                            EvapRefMedia = EvapRefMediaSecoMassaDagua[massaDAguaId]
                        elif not EvapRefMediaSecoMassaDagua:
                            EvapRefMedia = EvapRefMediaUmidoMassaDagua[massaDAguaId]
                        else:
                            EvapRefMedia = (EvapRefMediaUmidoMassaDagua[massaDAguaId]/EvapRefMediaSecoMassaDagua[massaDAguaId])
                        
                        cursorDestino.insertRow((massaDAguaId, nomeMassaDagua[massaDAguaId], ano, mes, EvapRefMedia))

def calcularMediaHistoricaEvaporacaoReferenciaPorMassaDagua(camadaPontosMargemMassasDAgua, anoInicialHistorico, anoFinalHistorico):
    """
    Calcula a evapotranspira????o l??quida  hist??rica de cada massa dagua, para o per??odo informado.
    
    Evapora????o da massa d'??gua = Kw * Evapora????o de Refer??ncia 
    onde: 
       Kw =0,3814 NDWI * 0,5989
    
    Evapora????o l??quida da massa d'??gua = Evapora????o da massa d'??gua - EtReal (a evapora????o da massa d'??gua sempre ?? maior)

    Evapora????o l??quida da massa d'??gua m3/m??s = Evapora????o l??quida da massa d'??gua mm/m??s * ??rea em Ha da massa d'??gua * 10
    
    EvLiquida = Evapora????o Liquida Massa DAgua [ano, mes] * ??rea (ha) massa d'??gua[ano, mes] * 10   //para transformar de mm/m??s para m3/m??s
    
    @param camadaPontosMargemMassasDAgua: feature class dos pontos das margens das massas dagua
    @param int anoInicialHistorico: ano inicial a considerar do hist??rico de dados de evapora????o de referencia medio
    @param int anoFinalHistorico: ano final a considerar do hist??rico de dados de evapora????o de referencia medio
    
    """
    pymsg = ""
    msgs = ""
    
    try:
        
        for ano in range(anoInicialHistorico, anoFinalHistorico + 1):
        
            for mes in range(1,13):
            
                #Obtem os valores de evapora????o de refer??ncia, na etapa <ano,mes> a partir da superficie sintetica de evapora????o de refer??ncia
                
                #Monta nome raster evapora????o de refer??ncia m??dia por munic??pio referente ao per??do <ano,mes>
                nomeRasterEvapRefMediaMunicipio = "superficie_evaporacao_referencia_medio_municipio_" + str(ano) + "_" + str(mes)
                nomeRasterEvapRefMediaMunicipio = os.path.join(diretorioSuperficieEvapRefMediaMunicipio, nomeRasterEvapRefMediaMunicipio)
                
                if arcpy.Exists(nomeRasterEvapRefMediaMunicipio):
                
                    if mes in meses_periodo_umido:
                        estacao = 'Chuva'
                    elif mes in meses_periodo_seco:    
                        estacao = 'Seco'
                    else:
                        continue
                        
                    #Filtra a camada de pontos pelo ano e estacao corrente
                    camadaPontosMargemMassasDAgua_Layer = r"in_memory\camadaPontosMargemMassasDAgua_lyr"
                    arcpy.MakeFeatureLayer_management(camadaPontosMargemMassasDAgua,camadaPontosMargemMassasDAgua_Layer)
                    
                    sqlWhere = Constantes.NOME_ATRIBUTO_ANO + " = "  + str(ano) + " AND " + Constantes.NOME_ATRIBUTO_ESTACAO + " = " + "'" + estacao + "'" 
                    arcpy.SelectLayerByAttribute_management (camadaPontosMargemMassasDAgua_Layer, "NEW_SELECTION", sqlWhere) 
                    
                    #Extrai o valores de evapora????o de referencia do raster nomeRasterEvapRefMediaMunicipio
                    camadaPontosValoresEvapRef = r"in_memory\camadaValoresEvapRefPontosMargemMassasDAgua"
                    ExtractValuesToPoints(camadaPontosMargemMassasDAgua_Layer, nomeRasterEvapRefMediaMunicipio, camadaPontosValoresEvapRef)
                    
                    #Calcula a m??dia da evapora????o de referencia de cada massa dagua (m??dia dos pontos do pol??gono)
                    tabelaSumarizada = r"in_memory\tabela_sumarizada"
                    nomeAtributoEstatisticaEvapRef = "RASTERVALU"
                    estatistica = [[nomeAtributoEstatisticaEvapRef, 'MEAN']]  
                    atributoAgregador = "gid;nmoriginal"
                    
                    arcpy.Statistics_analysis(camadaPontosValoresEvapRef, tabelaSumarizada, estatistica, atributoAgregador)
                    
                    #Armazena o evapora????o de referencia na tabela hist??ria
                    tabelaHistoricaEvapRefMedia = Constantes.TABELA_HISTORICO_EVAPREF_MEDIO_MASSA_DAGUA
                    
                    atributosOrigem = [Constantes.NOME_ATRIBUTO_CODIGO_MUNICIPIO, Constantes.NOME_ATRIBUTO_MASSA_DAGUA, 'MEAN_' + nomeAtributoEstatisticaEvapRef]
                    atributosDestino = [Constantes.NOME_ATRIBUTO_ID_MASSA_DAGUA, Constantes.NOME_ATRIBUTO_MASSA_DAGUA, Constantes.NOME_ATRIBUTO_ANO , Constantes.NOME_ATRIBUTO_MES, Constantes.NOME_ATRIBUTO_EVAPREF_MEDIO]
                    
                    with arcpy.da.SearchCursor(tabelaSumarizada, atributosOrigem) as cursorOrigem:
                        with arcpy.da.InsertCursor(tabelaHistoricaEvapRefMedia, atributosDestino) as cursorDestino:
                            for row in cursorOrigem:
                                cursorDestino.insertRow((row[0], row[1], ano, mes, row[2]))
                                
                    #libera a memoria utilizada  
                    arcpy.Delete_management("in_memory")
                    
        populaEvaporacaoReferenciaMediaMesesSemDados(tabelaHistoricaEvapRefMedia, anoInicialHistorico, anoFinalHistorico)
        
    except:
        
        # Get the traceback object
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        
        # Concatenate error information into message string
        pymsg = 'PYTHON ERRORS:\nTraceback info:\n{0}\nError Info:\n{1}'\
              .format(tbinfo, str(sys.exc_info()[1]))
        
        msgs = 'ArcPy ERRORS:\n {0}\n'.format(arcpy.GetMessages(2))
      
        # Return python error messages for script tool or Python Window
        arcpy.AddError(pymsg)
        arcpy.AddError(msgs)

    finally:
        
        if len(pymsg)>0 or len(msgs)>0:
            sys.exit(0)
   
def CalcularEvapotranspiracaoRealHistoricaMassasDAgua (shapefileMassaDAguaLandsatAgregado, shapefileMassaDAguaANA):
    """
    Calcula a evapotranspira????o real das Massas D'??gua artificiais identificadas nas imagens Landsat
    Metodologia: para cada massa d'??gua:
       1. Obtem do hist??rico de imagens, o pol??gono de maior ??rea;
       2. Faz um buffer de 1km ao redor do pol??gono a fim de extrair no pr??xino passo, pontos nas margens da massa d'??gua
       3. Extrai a evapotranspira????o real de todos os pontos de todas as massas d'??gua, a parir do raster do produto SSeBop Global
       4. Computa o EtReal m??dio dos pontos das margens de cada massa d'??gua  
    """

    pymsg = ""
    msgs = ""
    
    try:
        
        fc = shapefileMassaDAguaANA
        atributos = [Constantes.NOME_ATRIBUTO_ID_MASSA_DAGUA]

        #filtra Massas D'??gua identificadas
        sqlWhere = Constantes.NOME_ATRIBUTO_MASSA_DAGUA + " <>'' "
        
        with arcpy.da.SearchCursor(fc, atributos, where_clause=sqlWhere) as cursor:
            for massaDagua in cursor:
               
                massaDaguaId = int(massaDagua[0])
                
                definirPontosMargemMassaDaguaDeMaiorArea(massaDaguaId, shapefileMassaDAguaLandsatAgregado)
        
        calcularMediaHistoricaEvaportranspiracaoRealPorMassaDagua(Constantes.ARQUIVO_MAIOR_MASSA_DAGUA_PONTOS_MARGEM_AGREGADO,anoInicialHistorico, anoFinalHistorico)
        
    except:
        
        # Get the traceback object
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        
        # Concatenate error information into message string
        pymsg = 'PYTHON ERRORS:\nTraceback info:\n{0}\nError Info:\n{1}'\
              .format(tbinfo, str(sys.exc_info()[1]))
        
        msgs = 'ArcPy ERRORS:\n {0}\n'.format(arcpy.GetMessages(2))
      
        # Return python error messages for script tool or Python Window
        arcpy.AddError(pymsg)
        arcpy.AddError(msgs)

    finally:
        
        # Delete cursor objects to remove locks on the data 
        if cursor:
            del cursor

        if len(pymsg)>0 or len(msgs)>0:
            sys.exit(0)

def calcularMediaHistoricaEvaportranspiracaoRealPorMassaDagua(camadaPontosMargemMassasDAgua, anoInicialHistorico, anoFinalHistorico):
    """
    Calcula a m??dia da evapotranspira????o real (SSEBop) de cada massa dagua, para o hist??rico informado.
    A m??dia ?? calculada a partir dos pontos definidos das margens de cada massas d'agua.
    
    @param camadaPontosMargemMassasDAgua: feature class dos pontos das margens das massas dagua
    @param int anoInicialHistorico: ano inicial a considerar do hist??rico de dados do SSEBop Global
    @param int anoFinalHistorico: ano final a considerar do hist??rico de dados do SSEBop Global
    
    """
    
    pymsg = ""
    msgs = ""
    
    try:
        
        listaAnosSemDadosEtReal = []
        
        for ano in range(anoInicialHistorico, anoFinalHistorico + 1):
            
            #Monta nome do raster de evapotranspira????o real (SSEBop) referente ao per??do <ano,mes>
            nomeRasterSSEBop = "m" + str(ano) +  "01_modisSSEBopETv5_actual_mm_albers.tif"
            nomeRasterSSEBop = os.path.join(diretorioSSEBopGlobal, nomeRasterSSEBop)
            
            if not arcpy.Exists(nomeRasterSSEBop): 
                listaAnosSemDadosEtReal.append(ano)
                continue 
            
            for mes in range(1,13):
                
                #Obtem os valores reais de evapotranspira????o do SSeBop Global e da evapora????o de refer??ncia 
                
                #Monta nome do raster de evapotranspira????o real (SSEBop) referente ao per??do <ano,mes>
                nomeRasterSSEBop = "m" + str(ano) + str(mes).zfill(2) +  "_modisSSEBopETv5_actual_mm_albers.tif"
                nomeRasterSSEBop = os.path.join(diretorioSSEBopGlobal, nomeRasterSSEBop)

                #Monta nome raster evapora????o de refer??ncia m??dia por munic??pio referente ao per??do <ano,mes>
                nomeRasterEvapRefMediaMunicipio = "superficie_evaporacao_referencia_medio_municipio_" + str(ano) + "_" + str(mes)
                nomeRasterEvapRefMediaMunicipio = os.path.join(diretorioSuperficieEvapRefMediaMunicipio, nomeRasterEvapRefMediaMunicipio)
              
                if arcpy.Exists(nomeRasterSSEBop) and arcpy.Exists(nomeRasterEvapRefMediaMunicipio):
                
                    camadaPontosValores_EtReal_EvapRef_Kc = r"in_memory\camadaPontosMargemMassasDAgua"
                    arcpy.CopyFeatures_management(camadaPontosMargemMassasDAgua, camadaPontosValores_EtReal_EvapRef_Kc)

                    #Adiciona o atributo calculado Kc na camadaPontosValores_EtReal_EvapRef_Kc
                    arcpy.AddField_management(camadaPontosValores_EtReal_EvapRef_Kc, Constantes.NOME_ATRIBUTO_KC, "DOUBLE", "", "", "", "", "", "REQUIRED")

                    #Extrai os valores de evapotranspiracao real (SSEBop) e Evapora????o de Referencia dos rasters  
                    #para todos os pontos definidoas na camada verticesMargemMassasDAgua
                    ExtractMultiValuesToPoints(camadaPontosValores_EtReal_EvapRef_Kc, [[nomeRasterSSEBop, Constantes.NOME_ATRIBUTO_ETREAL], 
                                                                                      [nomeRasterEvapRefMediaMunicipio, Constantes.NOME_ATRIBUTO_EVAPREF]])

                    #Computa o valor de Kc, segundo a f??rmula: Kc = EtReal/EvapRef
                    expressao= "!EtReal!/!EvapRef!" 
                    arcpy.CalculateField_management(camadaPontosValores_EtReal_EvapRef_Kc, Constantes.NOME_ATRIBUTO_KC, expressao, "PYTHON_9.3")
                    
                    #Calcula a m??dia por massa d'??gua dos atributos EtReal, EvapRef e Kc
                    tabelaSumarizada = r"in_memory\tabela_sumarizada"
                    nomeAtributoEstatisticaEtReal = Constantes.NOME_ATRIBUTO_ETREAL
                    nomeAtributoEstatisticaEvapRef = Constantes.NOME_ATRIBUTO_EVAPREF
                    nomeAtributoEstatisticaKc = Constantes.NOME_ATRIBUTO_KC
                    estatistica = [[nomeAtributoEstatisticaEtReal, 'MEAN'], [nomeAtributoEstatisticaEvapRef, 'MEAN'], [nomeAtributoEstatisticaKc, 'MEAN']]  
                    atributoAgregador = "gid;nmoriginal"
                    
                    arcpy.Statistics_analysis(camadaPontosValores_EtReal_EvapRef_Kc, tabelaSumarizada, estatistica, atributoAgregador)
                    
                    #Armazena as medias na tabela hist??ria
                    tabelaHistoricaEtReal_EvapRef_Kc_Medio = Constantes.TABELA_HISTORICO_ETREAL_EVAPREF_KC_MEDIO_MASSA_DAGUA
                    
                    atributosOrigem = [Constantes.NOME_ATRIBUTO_ID_MASSA_DAGUA, Constantes.NOME_ATRIBUTO_MASSA_DAGUA, 'MEAN_' + nomeAtributoEstatisticaEtReal, 'MEAN_' + nomeAtributoEstatisticaEvapRef, 'MEAN_' + nomeAtributoEstatisticaKc]
                    atributosDestino = [Constantes.NOME_ATRIBUTO_ID_MASSA_DAGUA, Constantes.NOME_ATRIBUTO_MASSA_DAGUA, Constantes.NOME_ATRIBUTO_ANO , Constantes.NOME_ATRIBUTO_MES, Constantes.NOME_ATRIBUTO_ETREAL_MEDIO, Constantes.NOME_ATRIBUTO_EVAPREF_MEDIO, Constantes.NOME_ATRIBUTO_KC_MEDIO]
                    
                    with arcpy.da.SearchCursor(tabelaSumarizada, atributosOrigem) as cursorOrigem:
                        with arcpy.da.InsertCursor(tabelaHistoricaEtReal_EvapRef_Kc_Medio, atributosDestino) as cursorDestino:
                            for row in cursorOrigem:
                                cursorDestino.insertRow((row[0], row[1], ano, mes, row[2], row[3], row[4]))
                    
                    #libera a memoria utilizada  
                    arcpy.Delete_management("in_memory")
                    
        #Preenche os dados de EtReal para os anos em que n??o existem dados hist??ricos
        populaEtRealMedioAnosSemDadosHistoricos(listaAnosSemDadosEtReal, camadaPontosMargemMassasDAgua, tabelaHistoricaEtReal_EvapRef_Kc_Medio)
    
    except:
        
        # Get the traceback object
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        
        # Concatenate error information into message string
        pymsg = 'PYTHON ERRORS:\nTraceback info:\n{0}\nError Info:\n{1}'\
              .format(tbinfo, str(sys.exc_info()[1]))
        
        msgs = 'ArcPy ERRORS:\n {0}\n'.format(arcpy.GetMessages(2))
      
        # Return python error messages for script tool or Python Window
        arcpy.AddError(pymsg)
        arcpy.AddError(msgs)

    finally:
        
        if len(pymsg)>0 or len(msgs)>0:
            sys.exit(0)

def calcularKcMedioMensalPorMassaDAgua(tabelaHistoricaEtReal_EvapRef_Kc_Medio):
    """
        A partir dos dados hist??ricos de Kc existentes, 
        calcula-se a m??dia mensal para cada massa dagua e o armazena em uma tabela no formato
        [MassId, Massa, Mes, Kc]                      
    """
    
    #cria a tabela das medias mensais de Kc por Massa D'??gua
    configurarTabelaKcMensalMassaDAgua(Constantes.TABELA_KC_MENSAL_MASSA_DAGUA)

    nomeAtributoEstatistica = Constantes.NOME_ATRIBUTO_KC_MEDIO
    estatistica = nomeAtributoEstatistica + " MEAN"
    atributoAgregador = "gid;Mes"
    
    arcpy.Statistics_analysis(tabelaHistoricaEtReal_EvapRef_Kc_Medio, Constantes.TABELA_KC_MENSAL_MASSA_DAGUA, estatistica, atributoAgregador)
    
    return Constantes.TABELA_KC_MENSAL_MASSA_DAGUA
    
def populaEtRealMedioAnosSemDadosHistoricos(listaAnosSemDadosEtReal, camadaPontosMargemMassasDAgua, tabelaHistoricaEtReal_EvapRef_Kc_Medio):
    """
        Complementa o hist??rico da Evapotranspira????o Real (EtReal) de cada massa d'??gua, a partir do Kc m??dio 
        calculado do hist??rico existente do produto SSeBop Global (2003-2021). 
        Com base no Kc m??dio e da Evapora????o de refer??ncia, obtem-se o EtReal pela da aplica????o da f??rmula:
        EtReal = Kc * EvapRef (M??todo de Penman Montheif)
        
        @param feature class camadaPontosMargemMassasDAgua: camada de pontos das margens da representa????o de maior ??rea de cada massa d'??gua
        
    
    """
    
    #Computa o Kc m??dio mensal de cada massa d'??gua e o armazena na tabela Constantes.TABELA_KC_MENSAL_MASSA_DAGUA
    tabelaMediaMensalKc= calcularKcMedioMensalPorMassaDAgua(tabelaHistoricaEtReal_EvapRef_Kc_Medio)

    for ano in listaAnosSemDadosEtReal:
        for mes in range(1, 13):

            #Monta nome raster evapotranspira????o de refer??ncia m??dia por munic??pio referente ao per??do <ano,mes>
            nomeRasterEvapRefMediaMunicipio = "superficie_evaporacao_referencia_medio_municipio_" + str(ano) + "_" + str(mes)
            nomeRasterEvapRefMediaMunicipio = os.path.join(diretorioSuperficieEvapRefMediaMunicipio, nomeRasterEvapRefMediaMunicipio)
            
            if arcpy.Exists(nomeRasterEvapRefMediaMunicipio):
            
                camadaPontosValoresEvapRef = r"in_memory\camadaValoresEvapRefPontosMargemMassasDAgua"
                ExtractValuesToPoints(camadaPontosMargemMassasDAgua, nomeRasterEvapRefMediaMunicipio, camadaPontosValoresEvapRef)

                #Calcula a m??dia do atributo EvapRef para cada massa dagua
                tabelaSumarizada = r"in_memory\tabela_sumarizada"
                nomeAtributoEstatisticaEvapRef = "RASTERVALU"
                estatistica = [[nomeAtributoEstatisticaEvapRef, 'MEAN']]  
                atributoAgregador = "gid;nmoriginal"
                
                arcpy.Statistics_analysis(camadaPontosValoresEvapRef, tabelaSumarizada, estatistica, atributoAgregador)
                
                KcMedioPorMassaDAgua = {}
                sqlWhere = Constantes.NOME_ATRIBUTO_MES + ' = ' + str(mes)
                atributosOrigem = [Constantes.NOME_ATRIBUTO_ID_MASSA_DAGUA, 'MEAN_' + Constantes.NOME_ATRIBUTO_KC_MEDIO]
                with arcpy.da.SearchCursor(tabelaMediaMensalKc, atributosOrigem, where_clause=sqlWhere) as cursor:
                    for row in cursor:
                        KcMedioPorMassaDAgua[row[0]] = row[1]
                
                #Insere valores EvapRef na tabela historica tabelaHistoricaEtReal_EvapRef_Kc_Medio
                atributosOrigem = [Constantes.NOME_ATRIBUTO_ID_MASSA_DAGUA, Constantes.NOME_ATRIBUTO_MASSA_DAGUA, 'MEAN_' + nomeAtributoEstatisticaEvapRef]
                atributosDestino = [Constantes.NOME_ATRIBUTO_ID_MASSA_DAGUA, Constantes.NOME_ATRIBUTO_MASSA_DAGUA, Constantes.NOME_ATRIBUTO_ANO, Constantes.NOME_ATRIBUTO_MES, Constantes.NOME_ATRIBUTO_ETREAL_MEDIO, Constantes.NOME_ATRIBUTO_EVAPREF_MEDIO, Constantes.NOME_ATRIBUTO_KC_MEDIO]
                
                with arcpy.da.SearchCursor(tabelaSumarizada, atributosOrigem) as cursorOrigem:
                    with arcpy.da.InsertCursor(tabelaHistoricaEtReal_EvapRef_Kc_Medio, atributosDestino) as cursorDestino:
                        for row in cursorOrigem:
                            
                            # Obterm o Kc medio da Massa DAgua referente ao m??s = mes
                            KcMedio = KcMedioPorMassaDAgua[row[0]]
                            
                            # calcula o EtReal Medio (EtReal = Kc * EvapRef)
                            EtRealMedio = KcMedio * row[2] 
                            
                            cursorDestino.insertRow((row[0], row[1], ano, mes, EtRealMedio, row[2], KcMedio))
                
                #libera a memoria utilizada  
                arcpy.Delete_management("in_memory")
    
def obterMassaDAguaDeMaiorArea(massaDaguaId, shapefileMassaDAguaLandsatAgregado):
    """
    Retorna o poligono da massa dagua de mairo area, a partir da camada historica agregada de massas dagua
    @param str nomeMassaDagua: nome da massa dagua
    
    @return: 
    """
    pymsg = ""
    msgs = ""
    
    try:
        
        fc = shapefileMassaDAguaLandsatAgregado
        atributos=[Constantes.NOME_ATRIBUTO_AREA, 'SHAPE@', Constantes.NOME_ATRIBUTO_MASSA_DAGUA, Constantes.NOME_ATRIBUTO_ID_MASSA_DAGUA, Constantes.NOME_ATRIBUTO_ANO, Constantes.NOME_ATRIBUTO_ESTACAO]
        
        sqlWhere = Constantes.NOME_ATRIBUTO_ID_MASSA_DAGUA + " = " + str(massaDaguaId)
        
        maiorMassaDAgua=''
        for row in sorted(arcpy.da.SearchCursor(fc, atributos, sqlWhere),  reverse=True):
            maiorMassaDAgua = row
            break
        
        return maiorMassaDAgua;
    
    except:
        
        # Get the traceback object
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        
        # Concatenate error information into message string
        pymsg = 'PYTHON ERRORS:\nTraceback info:\n{0}\nError Info:\n{1}'\
              .format(tbinfo, str(sys.exc_info()[1]))
        
        msgs = 'ArcPy ERRORS:\n {0}\n'.format(arcpy.GetMessages(2))
      
        # Return python error messages for script tool or Python Window
        arcpy.AddError(pymsg)
        arcpy.AddError(msgs)

    finally:
        
        if len(pymsg)>0 or len(msgs)>0:
            sys.exit(0)

    
def definirPontosMargemMassaDaguaDeMaiorArea(idMassaDagua, shapefileMassaDAguaLandsatAgregado):
    '''
    returns a set a ponint shapefile, containing a set of points taken
    from the margin of the water body. 
    '''

    pymsg = ""
    msgs = ""
    
    try:
        
        maiorMassaDAgua= obterMassaDAguaDeMaiorArea(idMassaDagua, shapefileMassaDAguaLandsatAgregado)
        if maiorMassaDAgua:
            
            areaMassaDAgua = maiorMassaDAgua[0]
            shapeMaiorMassaDAgua = maiorMassaDAgua[1]
            nomeMassaDagua = maiorMassaDAgua[2]
            ano = maiorMassaDAgua[4]
            estacao = maiorMassaDAgua[5]
            
            arcpy.CopyFeatures_management(shapeMaiorMassaDAgua, "maiorMassaDAguaPersistido")
    
            # Buffer de 1km (mesma resolu????o espacial do raster SSeBop Global, usado para obter a Evapotranspira????o )
            buffer1kmEmMemoria = "in_memory\Buff1km"
            arcpy.Buffer_analysis("maiorMassaDAguaPersistido", buffer1kmEmMemoria, "1000 Meters", "OUTSIDE_ONLY", "ROUND", "ALL", "", "PLANAR")
    
            mergeEmMemoria = "in_memory\Merge"
            arcpy.management.Merge(["maiorMassaDAguaPersistido", buffer1kmEmMemoria], mergeEmMemoria)
            
            dissolveEmMemoria = "in_memory\Dissolve"
            arcpy.Dissolve_management(mergeEmMemoria, dissolveEmMemoria,"", "", "SINGLE_PART", "")
            
            #Simplifica a forma de poligono, de forma a reduzir o numero de vertices 
            tolerancia = obterToleranciaAlgortimoSimplificacao(areaMassaDAgua)
            
            simplifiedEmMEmoria= "in_memory\Simplified"
            CA.SimplifyPolygon(dissolveEmMemoria, simplifiedEmMEmoria, "POINT_REMOVE", tolerancia, "", "#", "NO_KEEP")

            verticesEmMemoria= "in_memory\Vertices"
            arcpy.FeatureVerticesToPoints_management(simplifiedEmMEmoria, verticesEmMemoria, "ALL")

            #Armazena em uma unica camada, os poligonos representando as maiores ??reas de cada massa dagua
            adicionarFeicaoCamadaAgregada(idMassaDagua, nomeMassaDagua, ano, estacao , "maiorMassaDAguaPersistido", Constantes.ARQUIVO_MAIOR_MASSA_DAGUA_AGREGADO)

            #Armazena em uma unica camada, o buffer dos poligonos representando as maiores ??reas de cada massa dagua
            adicionarFeicaoCamadaAgregada(idMassaDagua, nomeMassaDagua, ano, estacao, buffer1kmEmMemoria, Constantes.ARQUIVO_MAIOR_MASSA_DAGUA_AGREGADO_BUFFER_1KM)

            #Armazena em uma unica camada, a jun????o do buffer com os poligonos representando as maiores ??reas de cada massa dagua
            adicionarFeicaoCamadaAgregada(idMassaDagua, nomeMassaDagua, ano, estacao, dissolveEmMemoria, Constantes.ARQUIVO_MAIOR_MASSA_DAGUA_AGREGADO_DISSOLVE)

            #Armazena em uma unica camada, a simplifica????o dos poligonos representando as maiores ??reas de cada massa dagua
            adicionarFeicaoCamadaAgregada(idMassaDagua, nomeMassaDagua, ano, estacao, simplifiedEmMEmoria, Constantes.ARQUIVO_MAIOR_MASSA_DAGUA_AGREGADO_SIMPLIFY)
            
            #Armazena em uma unica camada, os pontos dos v??rtices dos dos poligonos simplificados das massas dagua
            adicionarFeicaoCamadaAgregada(idMassaDagua, nomeMassaDagua, ano, estacao, verticesEmMemoria, Constantes.ARQUIVO_MAIOR_MASSA_DAGUA_PONTOS_MARGEM_AGREGADO)
            
            #libera a memoria utilizada  
            arcpy.Delete_management("in_memory")
            
    except:
        
        # Get the traceback object
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        
        # Concatenate error information into message string
        pymsg = 'PYTHON ERRORS:\nTraceback info:\n{0}\nError Info:\n{1}'\
              .format(tbinfo, str(sys.exc_info()[1]))
        
        msgs = 'ArcPy ERRORS:\n {0}\n'.format(arcpy.GetMessages(2))
      
        # Return python error messages for script tool or Python Window
        arcpy.AddError(pymsg)
        arcpy.AddError(msgs)

    finally:
        
        if len(pymsg)>0 or len(msgs)>0:
            sys.exit(0)

def adicionarFeicaoCamadaAgregada(idMassaDagua, nomeMassaDAgua, ano, estacao, feicao, camadaAgregadaDestino):
    """
    """
    
    pymsg = ""
    msgs = ""

    try:
        
        atributosOrigem = ['SHAPE@']
        atributosDestino = ['SHAPE@', Constantes.NOME_ATRIBUTO_ID_MASSA_DAGUA, Constantes.NOME_ATRIBUTO_MASSA_DAGUA, Constantes.NOME_ATRIBUTO_ANO, Constantes.NOME_ATRIBUTO_ESTACAO]
        
        with arcpy.da.SearchCursor(feicao, atributosOrigem) as cursorOrigem:
            with arcpy.da.InsertCursor(camadaAgregadaDestino,atributosDestino) as cursorDestino:
                for row in cursorOrigem:
                    cursorDestino.insertRow((row[0], idMassaDagua, nomeMassaDAgua, ano, estacao))
            
    except:
  
        # Get the traceback object
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        
        # Concatenate error information into message string
        pymsg = 'PYTHON ERRORS:\nTraceback info:\n{0}\nError Info:\n{1}'\
              .format(tbinfo, str(sys.exc_info()[1]))
        
        msgs = 'ArcPy ERRORS:\n {0}\n'.format(arcpy.GetMessages(2))
      
        # Return python error messages for script tool or Python Window
        arcpy.AddError(pymsg)
        arcpy.AddError(msgs)

    finally:
        
            # Delete cursor objects to remove locks on the data 
            if cursorOrigem:
                del cursorOrigem
            if cursorDestino:
                del cursorDestino
    
            if len(pymsg)>0 or len(msgs)>0:
                sys.exit(0)
    
           
def obterToleranciaAlgortimoSimplificacao(areaMassaDagua):
    
    tolerancia = 0
    if 0 <= areaMassaDagua <= 1:
        tolerancia = 200
    elif 1 < areaMassaDagua <= 5:   
        tolerancia = 300
    elif 5 < areaMassaDagua <= 10:   
        tolerancia = 350
    elif 10 < areaMassaDagua <= 20:   
        tolerancia = 400
    else:   
        tolerancia = 500
    
    return tolerancia

def configurarTabelaKcMensalMassaDAgua(nomeTabela):
    """
    """   

    pymsg = ""
    msgs = ""
    
    try:
    
        # Exclue a tabela caso exista
        if arcpy.Exists(nomeTabela):
            arcpy.Delete_management(nomeTabela)

        nomeTabela = arcpy.CreateTable_management(arcpy.env.workspace, nomeTabela)

        nomeAtributo = Constantes.NOME_ATRIBUTO_ID_MASSA_DAGUA
        arcpy.AddField_management(nomeTabela, nomeAtributo, "lONG", "", "", "", "", "", "REQUIRED")

        nomeAtributo = Constantes.NOME_ATRIBUTO_MASSA_DAGUA
        arcpy.AddField_management(nomeTabela, nomeAtributo, "TEXT", "", "", "100", "", "", "REQUIRED")
        
        nomeAtributo = 'Mes'
        arcpy.AddField_management(nomeTabela, nomeAtributo, "SHORT", "", "", "", "", "", "REQUIRED")
                         
        nomeAtributo = Constantes.NOME_ATRIBUTO_KC_MEDIO
        arcpy.AddField_management(nomeTabela, nomeAtributo, "DOUBLE", "", "", "", "", "", "REQUIRED")

    except:
  
        # Get the traceback object
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        
        # Concatenate error information into message string
        pymsg = 'PYTHON ERRORS:\nTraceback info:\n{0}\nError Info:\n{1}'\
              .format(tbinfo, str(sys.exc_info()[1]))
        
        msgs = 'ArcPy ERRORS:\n {0}\n'.format(arcpy.GetMessages(2))
      
        # Return python error messages for script tool or Python Window
        arcpy.AddError(pymsg)
        arcpy.AddError(msgs)

    finally:
        
        if len(pymsg)>0 or len(msgs)>0:
            sys.exit(0)


def configurarTabelaEvapRefMediaMassaDAgua(nomeTabela):
    """
    """   

    pymsg = ""
    msgs = ""
    
    try:
    
        # Exclue a tabela caso exista
        if arcpy.Exists(nomeTabela):
            arcpy.Delete_management(nomeTabela)

        nomeTabela = arcpy.CreateTable_management(arcpy.env.workspace, nomeTabela)

        nomeAtributo = Constantes.NOME_ATRIBUTO_ID_MASSA_DAGUA
        arcpy.AddField_management(nomeTabela, nomeAtributo, "lONG", "", "", "", "", "", "REQUIRED")

        nomeAtributo = Constantes.NOME_ATRIBUTO_MASSA_DAGUA
        arcpy.AddField_management(nomeTabela, nomeAtributo, "TEXT", "", "", "100", "", "", "REQUIRED")
        
        nomeAtributo = Constantes.NOME_ATRIBUTO_ANO
        arcpy.AddField_management(nomeTabela, nomeAtributo, "SHORT", "", "", "", "", "", "REQUIRED")

        nomeAtributo = Constantes.NOME_ATRIBUTO_MES
        arcpy.AddField_management(nomeTabela, nomeAtributo, "SHORT", "", "", "", "", "", "REQUIRED")
                         
        nomeAtributo = Constantes.NOME_ATRIBUTO_EVAPREF_MEDIO
        arcpy.AddField_management(nomeTabela, nomeAtributo, "DOUBLE", "", "", "", "", "", "REQUIRED")

    except:
  
        # Get the traceback object
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        
        # Concatenate error information into message string
        pymsg = 'PYTHON ERRORS:\nTraceback info:\n{0}\nError Info:\n{1}'\
              .format(tbinfo, str(sys.exc_info()[1]))
        
        msgs = 'ArcPy ERRORS:\n {0}\n'.format(arcpy.GetMessages(2))
      
        # Return python error messages for script tool or Python Window
        arcpy.AddError(pymsg)
        arcpy.AddError(msgs)

    finally:
        
        if len(pymsg)>0 or len(msgs)>0:
            sys.exit(0)
    
def configurarTabelaETRealEvapRefMediaMassaDAgua(nomeTabela):
    """
    """   

    pymsg = ""
    msgs = ""
    
    try:
    
        # Exclue a tabela caso exista
        if arcpy.Exists(nomeTabela):
            arcpy.Delete_management(nomeTabela)

        nomeTabela = arcpy.CreateTable_management(arcpy.env.workspace, nomeTabela)

        nomeAtributo = Constantes.NOME_ATRIBUTO_ID_MASSA_DAGUA
        arcpy.AddField_management(nomeTabela, nomeAtributo, "lONG", "", "", "", "", "", "REQUIRED")

        nomeAtributo = Constantes.NOME_ATRIBUTO_MASSA_DAGUA
        arcpy.AddField_management(nomeTabela, nomeAtributo, "TEXT", "", "", "100", "", "", "REQUIRED")
        
        nomeAtributo = Constantes.NOME_ATRIBUTO_ANO
        arcpy.AddField_management(nomeTabela, nomeAtributo, "SHORT", "", "", "", "", "", "REQUIRED")

        nomeAtributo = Constantes.NOME_ATRIBUTO_MES
        arcpy.AddField_management(nomeTabela, nomeAtributo, "SHORT", "", "", "", "", "", "REQUIRED")
                         
        nomeAtributo = Constantes.NOME_ATRIBUTO_ETREAL_MEDIO
        arcpy.AddField_management(nomeTabela, nomeAtributo, "DOUBLE", "", "", "", "", "", "REQUIRED")

        nomeAtributo = Constantes.NOME_ATRIBUTO_EVAPREF_MEDIO
        arcpy.AddField_management(nomeTabela, nomeAtributo, "DOUBLE", "", "", "", "", "", "REQUIRED")

        nomeAtributo = Constantes.NOME_ATRIBUTO_KC_MEDIO
        arcpy.AddField_management(nomeTabela, nomeAtributo, "DOUBLE", "", "", "", "", "", "REQUIRED")

    except:
  
        # Get the traceback object
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        
        # Concatenate error information into message string
        pymsg = 'PYTHON ERRORS:\nTraceback info:\n{0}\nError Info:\n{1}'\
              .format(tbinfo, str(sys.exc_info()[1]))
        
        msgs = 'ArcPy ERRORS:\n {0}\n'.format(arcpy.GetMessages(2))
      
        # Return python error messages for script tool or Python Window
        arcpy.AddError(pymsg)
        arcpy.AddError(msgs)

    finally:
        
        if len(pymsg)>0 or len(msgs)>0:
            sys.exit(0)
    
def configurarCamadasMassaDAguaAgregadas():

    configurarCamadaMassaDAguaAgregada(nomeCamada = Constantes.ARQUIVO_MAIOR_MASSA_DAGUA_AGREGADO, 
                                       tipoGeometria = "POLYGON")

    configurarCamadaMassaDAguaAgregada(nomeCamada = Constantes.ARQUIVO_MAIOR_MASSA_DAGUA_AGREGADO_BUFFER_1KM, 
                                       tipoGeometria = "POLYGON")

    configurarCamadaMassaDAguaAgregada(nomeCamada = Constantes.ARQUIVO_MAIOR_MASSA_DAGUA_AGREGADO_DISSOLVE, 
                                       tipoGeometria = "POLYGON")

    configurarCamadaMassaDAguaAgregada(nomeCamada = Constantes.ARQUIVO_MAIOR_MASSA_DAGUA_AGREGADO_SIMPLIFY, 
                                       tipoGeometria = "POLYGON")

    configurarCamadaMassaDAguaAgregada(nomeCamada = Constantes.ARQUIVO_MAIOR_MASSA_DAGUA_PONTOS_MARGEM_AGREGADO, 
                                       tipoGeometria = "POINT")

    configurarCamadaMassaDAguaAgregada(nomeCamada = Constantes.ARQUIVO_HISTORICO_MASSA_DAGUA_AGREGADO_SIMPLIFY, 
                                       tipoGeometria = "POLYGON")

    configurarCamadaMassaDAguaAgregada(nomeCamada = Constantes.ARQUIVO_HISTORICO_MASSA_DAGUA_PONTOS_MARGEM_AGREGADO, 
                                       tipoGeometria = "POINT")

def configurarCamadaMassaDAguaAgregada(nomeCamada, tipoGeometria):
    """
    """   

    pymsg = ""
    msgs = ""
    
    try:
        
        # Exclue o arquivo caso exista
        if arcpy.Exists(nomeCamada):
            arcpy.Delete_management(nomeCamada)
    
        has_m = "DISABLED"
        has_z = "DISABLED"
        
        nomeCamada = arcpy.CreateFeatureclass_management(arcpy.env.workspace, nomeCamada, tipoGeometria, "", has_m, has_z)
      
        nomeAtributo = Constantes.NOME_ATRIBUTO_ID_MASSA_DAGUA
        arcpy.AddField_management(nomeCamada, nomeAtributo, "lONG", "", "", "", "", "", "REQUIRED")

        nomeAtributo = Constantes.NOME_ATRIBUTO_MASSA_DAGUA
        arcpy.AddField_management(nomeCamada, nomeAtributo, "TEXT", "", "", "100", "", "", "REQUIRED")
        
        nomeAtributo = Constantes.NOME_ATRIBUTO_ANO
        arcpy.AddField_management(nomeCamada, nomeAtributo, "long", "", "", "", "", "", "REQUIRED")

        nomeAtributo = Constantes.NOME_ATRIBUTO_ESTACAO
        arcpy.AddField_management(nomeCamada, nomeAtributo, "TEXT", "", "", "10", "", "", "REQUIRED")

    except:
  
        # Get the traceback object
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        
        # Concatenate error information into message string
        pymsg = 'PYTHON ERRORS:\nTraceback info:\n{0}\nError Info:\n{1}'\
              .format(tbinfo, str(sys.exc_info()[1]))
        
        msgs = 'ArcPy ERRORS:\n {0}\n'.format(arcpy.GetMessages(2))
      
        # Return python error messages for script tool or Python Window
        arcpy.AddError(pymsg)
        arcpy.AddError(msgs)

    finally:
        
        if len(pymsg)>0 or len(msgs)>0:
            sys.exit(0)
    
# input parameters
shapefileMassaDAguaLandsatAgregado = arcpy.GetParameterAsText(0)
shapefileMassaDAguaANA = arcpy.GetParameterAsText(1)
diretorioSSEBopGlobal = arcpy.GetParameterAsText(2)
diretorioSuperficieEvapRefMediaMunicipio = arcpy.GetParameterAsText(3)
diretorioSaida = arcpy.GetParameterAsText(4)
anoInicialHistorico = int(arcpy.GetParameterAsText(5))
anoFinalHistorico = int(arcpy.GetParameterAsText(6))

if not File.existFile(shapefileMassaDAguaLandsatAgregado):
    arcpy.AddError("Arquivo inexistente: {arquivo}".format(dir=shapefileMassaDAguaLandsatAgregado) )
    sys.exit(0)

if not File.existFile(shapefileMassaDAguaANA):
    arcpy.AddError("Arquivo inexistente: {arquivo}".format(dir=shapefileMassaDAguaANA) )
    sys.exit(0)

if not File.existFile(diretorioSaida):
    arcpy.AddError("Diretorio inexistente: {dir}".format(dir=diretorioSaida) )
    sys.exit(0)

if not File.existFile(diretorioSSEBopGlobal):
    arcpy.AddError("Diretorio inexistente: {dir}".format(dir=diretorioSSEBopGlobal) )
    sys.exit(0)

if not File.existFile(diretorioSuperficieEvapRefMediaMunicipio):
    arcpy.AddError("Diretorio inexistente: {dir}".format(dir=diretorioSuperficieEvapRefMediaMunicipio) )
    sys.exit(0)

# Verifica a existencia da licenca da extensao ArcGIS Spatial Analyst 
arcpy.CheckOutExtension("Spatial")

# Define o workspace de processamento 
arcpy.env.workspace = diretorioSaida

arcpy.env.overwriteOutput = True

desc = arcpy.Describe(shapefileMassaDAguaANA)
sistema_coordenadas = desc.spatialReference

arcpy.env.outputCoordinateSystem=sistema_coordenadas

configurarTabelaETRealEvapRefMediaMassaDAgua(Constantes.TABELA_HISTORICO_ETREAL_EVAPREF_KC_MEDIO_MASSA_DAGUA)
configurarCamadasMassaDAguaAgregadas()
configurarTabelaEvapRefMediaMassaDAgua(Constantes.TABELA_HISTORICO_EVAPREF_MEDIO_MASSA_DAGUA)

CalcularEvapotranspiracaoRealHistoricaMassasDAgua(shapefileMassaDAguaLandsatAgregado, shapefileMassaDAguaANA)    
CalcularEvaporacaoReferenciaHistoricaMassasDAgua(shapefileMassaDAguaLandsatAgregado)    

# A implementar:
CalcularEvaporacaoLiquidaHistoricaMassasDAgua(shapefileMassaDAguaLandsatAgregado)    

    
    
    

