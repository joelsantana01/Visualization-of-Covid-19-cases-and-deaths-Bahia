import streamlit as st
from streamlit_option_menu import option_menu
import folium
import pandas as pd
from geobr import read_municipality
import geopandas as gpd
from unidecode import unidecode
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from streamlit_folium import folium_static
from matplotlib.animation import FuncAnimation, PillowWriter


obitos =pd.read_csv("data/obitos_filtrado.csv")
geometrias = gpd.read_file("data/geometrias.geojson")
casos = pd.read_csv("data/casos_filtrados.csv")
pop = pd.read_csv("data/pop.csv")


obitos['DATA DA NOTIFICACAO'] = pd.to_datetime(obitos['DATA DA NOTIFICACAO']).dt.date #tirando a hora da data
casos['DATA DA NOTIFICACAO'] = pd.to_datetime(casos['DATA DA NOTIFICACAO'], format='%d/%m/%Y')

## FUNÇÕES

#funcoes para obitos
def agrupar_por_data(df):
# Agrupar por mês (utilizando o pd.Grouper com frequência mensal)
    df_agrupado = df.groupby(pd.Grouper(key='DATA DA NOTIFICACAO', freq='M'))['quantidade'].sum().reset_index()
    df_agrupado.rename(columns={'DATA DA NOTIFICACAO': 'data', 'quantidade': 'valor'}, inplace=True)
    return df_agrupado

def municipios_selecionados(municipios, obitos):
    if isinstance(municipios, str):  
        municipios = [municipios]

    if 'Todos municípios' not in municipios:
        municipios = [unidecode(m.upper().strip()) for m in municipios if pd.notna(m)]
        municipio_selecionado = obitos[obitos['name_muni'].isin(municipios)]
    else:
        municipio_selecionado = obitos

    return municipio_selecionado

def filtrar_por_idade(municipio_selecionado, idades_selecionadas):
    if idades_selecionadas:
        municipio_selecionado = municipio_selecionado[municipio_selecionado['faixa_etaria'].isin(idades_selecionadas)]
    return municipio_selecionado


def filtrar_por_genero(municipio_selecionado, genero):
    if isinstance(genero, str):  
        genero = [genero]
    if "Masculino" in genero and "Feminino" not in genero:  # Verifica se 'genero' não está vazio ou None
        municipio_selecionado = municipio_selecionado[municipio_selecionado['SEXO'] == 'M']
    elif "Feminino" in genero and "Masculino" not in genero:
        municipio_selecionado = municipio_selecionado[municipio_selecionado['SEXO'] == 'F']
    else:
        municipio_selecionado = municipio_selecionado
    return municipio_selecionado


def filtrar_por_comorbidade(municipio_selecionado,comorbidade): 
    if isinstance(comorbidade, str):  
        comorbidade = [comorbidade]
        
    if "Todas as pessoas" not in comorbidade:
        municipio_selecionado = municipio_selecionado[municipio_selecionado['LISTA COMORBIDADE'].isin(comorbidade)]
    
    else:
        municipio_selecionado = municipio_selecionado

    return municipio_selecionado


def filtrar_por_hospital(municipio_selecionado, Hospital):
    if isinstance(Hospital, str):  
        Hospital = [Hospital]
        
    Hospital = [unidecode(m.upper().strip()) for m in Hospital if pd.notna(m)]   
    municipio_selecionado = municipio_selecionado[municipio_selecionado['TIPO ORGAO'].isin(Hospital)]
        
    return municipio_selecionado


def data(data_inicial, data_final, municipio_selecionado):
    df = municipio_selecionado[(municipio_selecionado['DATA DA NOTIFICACAO'] >= pd.to_datetime(data_inicial)) & 
        (municipio_selecionado['DATA DA NOTIFICACAO'] <= pd.to_datetime(data_final))]
    return df

    
def cor_municipio(feature, quartis):
    quantidade = feature['properties'].get('quantidade', 0)  # Usar 0 se quantidade não existir

    # Atribuir cor com base nos quartis
    if quantidade <= quartis[0]:  # 25% menores quantidades
        return "#E1D9F2"  # Roxo Claro
    elif quartis[0] < quantidade <= quartis[1]:  # Entre 25% e 50%
        return "#C69DE0"  # Roxo Médio Claro
    elif quartis[1] < quantidade <= quartis[2]:  # Entre 50% e 75%
        return "#8E44AD"  # Roxo Médio Escuro
    else:  # 25% maiores quantidades
        return "#4A007E"  # Roxo Escuro
    
def cor_taxa_municipio(feature, quartis):
    taxa = feature['properties'].get('taxas', 0)  # Usar 0 se taxa não existir

# Atribuir cor com base nos quartis das taxas
    if taxa <= quartis[0]:  # 25% menores taxas
        return "#E1D9F2"  # Azul Claro
    elif quartis[0] < taxa <= quartis[1]:  # Entre 25% e 50%
        return "#C69DE0"  # Roxo Claro
    elif quartis[1] < taxa <= quartis[2]:  # Entre 50% e 75%
        return "#8E44AD"  # Roxo Médio Escuro
    else:  # 25% maiores taxas
        return "#4A007E"  # Roxo Escuro

#'#F1E0FF''#D29EFF''#9B4D98''#5D0071'
#funcoes para casos
def municipios_selecionados_casos(municipios, casos):
    if isinstance(municipios, str):  
        municipios = [municipios]

    if 'Todos municípios' not in municipios:
        municipios = [unidecode(m.upper().strip()) for m in municipios if pd.notna(m)]
        municipio_selecionado = casos[casos['name_muni'].isin(municipios)]
    else:
        municipio_selecionado = casos

    return municipio_selecionado

def filtrar_por_idade_casos(municipio_selecionado, idades_selecionadas):
    if idades_selecionadas:
        municipio_selecionado = municipio_selecionado[municipio_selecionado['faixa_etaria'].isin(idades_selecionadas)]
    return municipio_selecionado

# colocar funcao para raca/cor, profissinal de saude 

def filtrar_por_genero_casos(municipio_selecionado, genero):
    if isinstance(genero, str):  
        genero = [genero]
    if "Masculino" in genero and "Feminino" not in genero:
        municipio_selecionado = municipio_selecionado[municipio_selecionado['SEXO'] == 'M']
    elif "Feminino" in genero and "Masculino" not in genero:
        municipio_selecionado = municipio_selecionado[municipio_selecionado['SEXO'] == 'F']
    else:
        municipio_selecionado = municipio_selecionado
    return municipio_selecionado

def data_casos(data_inicial, data_final, municipio_selecionado):
    municipio_selecionado = municipio_selecionado[(municipio_selecionado['DATA DA NOTIFICACAO'] >= pd.to_datetime(data_inicial)) & 
        (municipio_selecionado['DATA DA NOTIFICACAO'] <= pd.to_datetime(data_final))]
    return municipio_selecionado

def calcular_taxas(df_filtrado, taxa, pop):
# Inicializando a coluna de taxas com zero
    df_filtrado['taxas'] = 0

    if taxa == "Casos absolutos":
        df_filtrado = df_filtrado

    elif taxa == "Taxa por população":

        pop.rename(columns={"Unnamed: 1": "populacao"}, inplace=True)

    
        df_filtrado['name_muni'] = df_filtrado['name_muni'].str.strip()
        pop['População Residente - Estimativas para o TCU - Bahia'] = pop['População Residente - Estimativas para o TCU - Bahia'].str.strip()

    
        df_filtrado = df_filtrado.merge(pop, 
                                    left_on="name_muni", 
                                    right_on="População Residente - Estimativas para o TCU - Bahia", 
                                    how="left")

    
        df_filtrado['quantidade'] = pd.to_numeric(df_filtrado['quantidade'], errors='coerce')
        df_filtrado['populacao'] = pd.to_numeric(df_filtrado['populacao'], errors='coerce')

    
        df_filtrado['taxas'] = (df_filtrado['quantidade'] / df_filtrado['populacao']) *100
        df_filtrado['taxas'] = df_filtrado['taxas'].fillna(0)

    return df_filtrado




municipios = read_municipality(year=2020)
municipios_bahia = municipios[municipios["abbrev_state"] == "BA"]
todos_municipios = pd.DataFrame({"name_muni": ["Todos municípios"], "abbrev_state": ["BA"]})
municipios_bahia = pd.concat([todos_municipios, municipios_bahia], ignore_index=True)

opcoes_idade = ["0 a 10", "11 a 20", "21 a 30", "31 a 40", "41 a 50",
                "51 a 60", "61 a 70", "71 a 80", "81 a 90", "91 a 100", "100+"]

#nome diferente do df_filtrado para não dar problema no merge
geometrias['quantidade_z'] = 0
quartis = np.percentile(geometrias['quantidade_z'], [25, 50, 75])    


# Configuração da página
st.set_page_config(page_title="Página Principal", page_icon="📊", layout="wide")



with st.sidebar:
    choose = option_menu("", ["Home", "Mapas Interativos", "Séries Temporais","Mapas Espaço-Temporais", "Sobre o Autor"],
                         icons=['house', 'geo-alt', 'graph-up','map', 'person'],
                         default_index=0,
                         orientation="vertical",  
                         styles={
                             "container": {"padding": "5!important", "background-color": "#fafafa"},
                             "icon": {"color": "orange", "font-size": "25px"},
                             "nav-link": {"font-size": "16px", "text-align": "left", "margin": "0px", "--hover-color": "#eee"},
                             "nav-link-selected": {"background-color": "#02ab21"},
                         }, key="menu")



if choose == "Home":
    st.title("**Análise Visual e Interativa da COVID-19 (2020-2024)**")

    st.write("""
**Explore os dados da COVID-19!**  
Acesse gráficos dinâmicos e mapas detalhados que mostram a evolução da pandemia na **Bahia** ao longo de quatro anos.  
Personalize suas análises e mergulhe nas tendências **temporais e espaciais** da doença.

📊 **Principais Funcionalidades:**
- **Mapas Interativos**: Visualize os dados por município e personalize com base em diversos filtros.
- **Gráficos Dinâmicos**: Acompanhe a evolução dos casos e óbitos com gráficos de **séries temporais**, que mostram o comportamento da pandemia ao longo do tempo.

🔍 **Como Funciona?**
- Personalize as visualizações utilizando os filtros disponíveis.
- Veja como a pandemia se espalhou pela Bahia e observe as flutuações nos casos e óbitos ao longo do tempo, tanto de forma **espacial** quanto **temporal**.
""")

    st.subheader("📍 O que são Análises Espaciais e Séries Temporais?")

    st.write("""
**Estatística Espacial** trata da análise de dados de superfícies contínuas, pontuais ou de áreas. Observa como os eventos se distribuem no espaço e como essas distribuições podem ser influenciadas por proximidade e contexto geográfico.  
Através de técnicas como o **Índice de Moran**, **Semivariograma**, **Matriz de Mantel**, dentre outras, é possível identificar relações espaciais entre áreas e visualizar clusters que necessitam de atenção.

**Séries Temporais**, por outro lado, analisam dados ao longo do tempo, permitindo identificar tendências, ciclos e sazonalidades.  
Através de gráficos dinâmicos, podemos observar como os casos e óbitos de COVID-19 mudam ao longo do tempo, ajudando a prever futuros aumentos ou quedas, além de identificar picos e períodos sazonais.

**Fonte dos Dados:**  
Todos os dados são provenientes da **Secretaria da Saúde do Estado da Bahia (SESAB)**, com a última atualização em **10 de outubro de 2024**.

🚨 **Navegue pelas páginas de Mapas e Séries Temporais para explorar mais!**
""")

    st.subheader("🎯 Vamos começar a explorar?")
    st.write("Escolha uma opção no menu ao lado para começar sua jornada na análise interativa da pandemia.")


elif choose == "Mapas Interativos":


    st.title("🗺️ Mapas Interativos da Covid-19 na Bahia")
    st.write("**Personalize o Mapa com Base nos Filtros Abaixo:**")
    

    dados = st.selectbox("Deseja filtrar por casos ou óbitos?",['Casos','Óbitos'])



    if dados == 'Óbitos':
        
        municipios = st.multiselect('Escolha o municipio de interesse: ', municipios_bahia['name_muni'], placeholder= "Clique nas opções")

        data_inicial = st.date_input('Data de início (AAAA/MM/DD)')
        data_final = st.date_input('Data de fim (AAAA/MM/DD)')
          
        idades_selecionadas = st.multiselect("Você deseja mapear por qual intervalo de idades?", opcoes_idade , placeholder= "Clique nas opções")
        
        genero = st.multiselect("Selecione o gênero: ", ["Masculino", "Feminino"], placeholder= "Clique nas opções")
        
        comorbidade = st.multiselect('A pessoa tinha alguma comorbidade?', ["Sim", "Não","Todas as pessoas"], placeholder= "Clique nas opções")
                                             
        
        Hospital = st.multiselect("Qual tipo de hospital?", ["Público","Privado","Filantrópico"], placeholder= "Clique nas opções")
        
        taxa = st.selectbox("Como deseja mapear os dados?", ["Óbitos absolutos", "Taxa por população"], placeholder="Escolha uma opção")
        
    elif dados == 'Casos':
        
        municipios = st.multiselect('Escolha o municipio de interesse: ', municipios_bahia['name_muni'], placeholder= "Clique nas opções")

        data_inicial = st.date_input('Data de início (AAAA/MM/DD)')
        data_final = st.date_input('Data de fim (AAAA/MM/DD)')
          
        idades_selecionadas = st.multiselect("Você deseja mapear por qual intervalo de idades?", opcoes_idade , placeholder= "Clique nas opções")
        
        genero = st.multiselect("Selecione o gênero: ", ["Masculino", "Feminino"], placeholder= "Clique nas opções")
        
        taxa = st.selectbox("Como deseja mapear os dados?", ["Casos absolutos"], placeholder="Escolha uma opção")


    

    mapa_bahia = folium.Map(location=[-13.0000, -40.0000], zoom_start=6)

    
    col1, col2, col3 = st.columns([1, 0.3, 1]) #botão submeter centralizado

    with col2:
        submeter = st.button("SUBMETER")
        


    if submeter and dados == "Óbitos":
        municipio_selecionado = municipios_selecionados(municipios, obitos)
        municipio_selecionado['DATA DA NOTIFICACAO'] = pd.to_datetime(municipio_selecionado['DATA DA NOTIFICACAO'])
        municipio_selecionado = data(data_inicial, data_final, municipio_selecionado) 
        municipio_selecionado = filtrar_por_idade(municipio_selecionado, idades_selecionadas)
        municipio_selecionado = filtrar_por_genero(municipio_selecionado, genero)
        municipio_selecionado = filtrar_por_comorbidade(municipio_selecionado, comorbidade)
        municipio_selecionado = filtrar_por_hospital(municipio_selecionado, Hospital)
        df_filtrado = municipio_selecionado.groupby('name_muni')['quantidade'].sum().reset_index()
        df_filtrado = calcular_taxas(df_filtrado,taxa,pop)
        if "Óbitos absolutos" in taxa:
            df_filtrado = geometrias.merge(
                df_filtrado[['name_muni', 'quantidade']], 
                left_on='name_muni', 
                right_on='name_muni', 
                how='left'
                )
        
            df_filtrado = df_filtrado.fillna(0)
            geometrias = df_filtrado
            quartis = np.percentile(geometrias['quantidade'], [25, 50, 75])

            folium.GeoJson(
                geometrias,
                style_function=lambda feature: {
                    'fillColor': cor_municipio(feature, quartis),
                    'color': 'black',
                    'weight': 1,
                    'fillOpacity': 0.7
                    },
                tooltip=folium.GeoJsonTooltip(
                    fields=['name_muni', 'quantidade'], 
                    aliases=['Município:', 'Quantidade:'],  
                    localize=True
            
            )
            ).add_to(mapa_bahia)
        elif "Taxa por população" in taxa:
            df_filtrado = geometrias.merge(
                df_filtrado[['name_muni', 'taxas']], 
                left_on='name_muni', 
                right_on='name_muni', 
                how='left'
                )
            df_filtrado = df_filtrado.fillna(0)
            geometrias = df_filtrado
            quartis = np.percentile(geometrias['taxas'], [25, 50, 75])

            # Adicionando a camada GeoJson ao mapa
            folium.GeoJson(
                geometrias,
                style_function=lambda feature: {
                    'fillColor': cor_taxa_municipio(feature, quartis),
                    'color': 'black',
                    'weight': 1,
                    'fillOpacity': 0.7
                    },
                tooltip=folium.GeoJsonTooltip(
                    fields=['name_muni', 'taxas'], 
                    aliases=['Município:', 'taxas:'], 
                    localize=True
                    )
                ).add_to(mapa_bahia)

    elif submeter and dados == "Casos":
        
        municipio_selecionado = municipios_selecionados_casos(municipios, casos)
        municipio_selecionado['DATA DA NOTIFICACAO'] = pd.to_datetime(municipio_selecionado['DATA DA NOTIFICACAO'])
        municipio_selecionado = data_casos(data_inicial, data_final, municipio_selecionado) 
        municipio_selecionado = filtrar_por_idade_casos(municipio_selecionado, idades_selecionadas)
        municipio_selecionado = filtrar_por_genero_casos(municipio_selecionado, genero)
        df_filtrado = municipio_selecionado.groupby('name_muni')['quantidade'].sum().reset_index()
        df_filtrado = calcular_taxas(df_filtrado,taxa,pop)
        if "Casos absolutos" in taxa:
            df_filtrado = geometrias.merge(
                df_filtrado[['name_muni', 'quantidade']], 
                left_on='name_muni', 
                right_on='name_muni', 
                how='left'
                )
        
            df_filtrado = df_filtrado.fillna(0)
            geometrias = df_filtrado
            quartis = np.percentile(geometrias['quantidade'], [25, 50, 75])

            # Adicionando a camada GeoJson ao mapa
            folium.GeoJson(
                geometrias,
                style_function=lambda feature: {
                    'fillColor': cor_municipio(feature, quartis),
                    'color': 'black',
                    'weight': 1,
                    'fillOpacity': 0.7
                    },
                tooltip=folium.GeoJsonTooltip(
                    fields=['name_muni', 'quantidade'], 
                    aliases=['Município:', 'Quantidade:'], 
                    localize=True
            
            )
            ).add_to(mapa_bahia)
        elif "Taxa por população" in taxa:
            df_filtrado = geometrias.merge(
                df_filtrado[['name_muni', 'taxas']], 
                left_on='name_muni', 
                right_on='name_muni', 
                how='left'
                )
            df_filtrado = df_filtrado.fillna(0)
            geometrias = df_filtrado
            quartis = np.percentile(geometrias['taxas'], [25, 50, 75])

            
            folium.GeoJson(
                geometrias,
                style_function=lambda feature: {
                    'fillColor': cor_taxa_municipio(feature, quartis),
                    'color': 'black',
                    'weight': 1,
                    'fillOpacity': 0.7
                    },
                tooltip=folium.GeoJsonTooltip(
                    fields=['name_muni', 'taxas'],  
                    aliases=['Município:', 'taxas:'],  
                    localize=True
                    )
                ).add_to(mapa_bahia)



    # Exibir o mapa
    from streamlit_folium import folium_static
    folium_static(mapa_bahia, width=1000)   
        
        
        

    #lembrar de criar o linkedin

    # rodapé

elif choose == "Séries Temporais":
    st.title("📈 Séries Temporais da Covid-19 na Bahia")
    st.write("**Personalize o Gráfico com Base nos Filtros Abaixo:**")
    
    dados = st.selectbox("Deseja filtrar por casos ou óbitos?", ['Casos', 'Óbitos'])
    df_municipios = {}

    if dados == 'Óbitos':
        municipios = st.multiselect('Escolha o municipio de interesse: ', municipios_bahia['name_muni'], placeholder= "Clique nas opções")
        data_inicial = st.date_input('Data de início (AAAA/MM/DD)')
        data_final = st.date_input('Data de fim (AAAA/MM/DD)')
        idades_selecionadas = st.multiselect("Você deseja mapear por qual intervalo de idades?", opcoes_idade , placeholder= "Clique nas opções")
        genero = st.multiselect("Selecione o gênero: ", ["Masculino", "Feminino"], placeholder= "Clique nas opções")
        comorbidade = st.multiselect('A pessoa tinha alguma comorbidade?', ["Sim", "Não", "Todas as pessoas"], placeholder= "Clique nas opções")
        Hospital = st.multiselect("Qual tipo de hospital?", ["Público", "Privado", "Filantrópico"], placeholder= "Clique nas opções")

    elif dados == 'Casos':
        municipios = st.multiselect('Escolha o municipio de interesse: ', municipios_bahia['name_muni'], placeholder= "Clique nas opções")
        data_inicial = st.date_input('Data de início (AAAA/MM/DD)')
        data_final = st.date_input('Data de fim (AAAA/MM/DD)')
        idades_selecionadas = st.multiselect("Você deseja mapear por qual intervalo de idades?", opcoes_idade , placeholder= "Clique nas opções")
        genero = st.multiselect("Selecione o gênero: ", ["Masculino", "Feminino"], placeholder= "Clique nas opções")

    col1, col2, col3 = st.columns([1, 0.3, 1])

    with col2:
        submeter = st.button("SUBMETER")


    if submeter and dados == "Óbitos":
        municipio_selecionado = municipios_selecionados(municipios, obitos)
        municipio_selecionado['DATA DA NOTIFICACAO'] = pd.to_datetime(municipio_selecionado['DATA DA NOTIFICACAO'])
        municipio_selecionado = data(data_inicial, data_final, municipio_selecionado)
        municipio_selecionado = filtrar_por_idade(municipio_selecionado, idades_selecionadas)
        municipio_selecionado = filtrar_por_genero(municipio_selecionado, genero)
        municipio_selecionado = filtrar_por_comorbidade(municipio_selecionado, comorbidade)
        municipio_selecionado = filtrar_por_hospital(municipio_selecionado, Hospital)

        
        for municipio in municipio_selecionado['name_muni'].unique():
            municipio_df = municipio_selecionado[municipio_selecionado['name_muni'] == municipio]
            df_municipios[municipio] = municipio_df

    # Agrupando os dados por município
        for municipio, df in df_municipios.items():
            df_municipios[municipio] = agrupar_por_data(df)

    elif submeter and dados == "Casos":
        municipio_selecionado = municipios_selecionados_casos(municipios, casos)
        municipio_selecionado['DATA DA NOTIFICACAO'] = pd.to_datetime(municipio_selecionado['DATA DA NOTIFICACAO'])
        municipio_selecionado = data_casos(data_inicial, data_final, municipio_selecionado)
        municipio_selecionado = filtrar_por_idade_casos(municipio_selecionado, idades_selecionadas)
        municipio_selecionado = filtrar_por_genero_casos(municipio_selecionado, genero)

    # Criando um dicionário para separar os municípios em DataFrames
        df_municipios = {}
        for municipio in municipio_selecionado['name_muni'].unique():
            municipio_df = municipio_selecionado[municipio_selecionado['name_muni'] == municipio]
            df_municipios[municipio] = municipio_df

    # Agrupando os dados por município
        for municipio, df in df_municipios.items():
            df_municipios[municipio] = agrupar_por_data(df)

# Agora, criar um DataFrame único para plotar
    df_plot = pd.DataFrame()

# Verifica se há dados em df_municipios
    if df_municipios:
    # Loop para combinar todos os DataFrames em um único DataFrame
        for municipio, df in df_municipios.items():
            df['municipio'] = municipio  # Adiciona a coluna de município para diferenciação
            df_plot = pd.concat([df_plot, df], ignore_index=True)

        plt.figure(figsize=(10, 6))

        if len(df_municipios) == 1:
        # Se há apenas 1 município, plotar uma única linha
            sns.lineplot(data=df_plot, x='data', y='valor', label=df_plot['municipio'].iloc[0])
        else:
                # Se há mais de 1 município, plotar múltiplas linhas com `hue` para diferenciá-los
            sns.lineplot(data=df_plot, x='data', y='valor', hue='municipio')

        # Configuração do gráfico
        plt.title('Série Temporal de COVID-19')
        plt.xlabel('Datas')
        plt.ylabel('Quantidade')


    # Exibindo o gráfico
        st.pyplot(plt)
    else:
        st.write("Não há dados para exibir. Verifique os filtros aplicados.")

       
elif choose == "Mapas Espaço-Temporais":
    st.title("Mapas Espaço-Temporais")

    dados = st.selectbox("Deseja filtrar por casos ou óbitos?", ['Casos', 'Óbitos'])

    if dados == 'Óbitos':
        municipios = st.multiselect('Escolha o municipio de interesse: ',municipios_bahia['name_muni'], placeholder="Clique nas opções")
        escolha_ano = st.selectbox("Escolha o ano que deseja filtrar",["2020","2021","2022","2023","2024"])
        agrupamento = st.selectbox("Deseja agrupar por?", ["Semanal"], placeholder="Clique nas opções")


    elif dados == 'Casos':
        municipios = st.multiselect('Escolha o municipio de interesse: ', 
                                  municipios_bahia['name_muni'], 
                                  placeholder="Clique nas opções")
        escolha_ano = st.selectbox("Escolha o ano que deseja filtrar", 
                                 ["2020","2021","2022","2023","2024"])
        agrupamento = st.selectbox("Deseja agrupar por?", 
                                  ["Semanal"], 
                                  placeholder="Clique nas opções")


    col1, col2, col3 = st.columns([1, 0.3, 1])
    with col2:
        submeter = st.button("SUBMETER")

    if submeter and dados == "Óbitos":
        
        municipio_selecionado = municipios_selecionados(municipios, obitos)
        municipio_selecionado["DATA DA NOTIFICACAO"] = pd.to_datetime(municipio_selecionado["DATA DA NOTIFICACAO"], errors="coerce" )
        escolha_ano_int = int(escolha_ano)
        municipio_selecionado = municipio_selecionado[municipio_selecionado["DATA DA NOTIFICACAO"].dt.year == escolha_ano_int]
            
        if agrupamento == "Semanal":
            municipio_selecionado['semanas'] = municipio_selecionado['DATA DA NOTIFICACAO'].dt.isocalendar().week
                
            df_filtrado = (
                    municipio_selecionado.groupby(['semanas', 'name_muni']).size()
                    .unstack(fill_value=0)
                    .sort_index()
                    .cumsum()
                )


            bahia = read_municipality(code_muni=29, year=2019)
            bahia['name_muni'] = [unidecode(m).upper().strip() if pd.notna(m) else m for m in bahia['name_muni']]

            
            def preparar_df_semana(casos_semana, semana):
                df = bahia.copy()
    
                if semana in casos_semana.index:
                    casos_df = casos_semana.loc[semana].reset_index()
                    casos_df.columns = ['name_muni', 'casos'] 
        
                    df = df.merge(casos_df, on='name_muni', how='left')
                    df['casos'] = df['casos'].fillna(0) 
                else:
                    df['casos'] = 0
    
                return df

            def animar_mapa(casos, semanas, ano, nome_arquivo):
                fig, ax = plt.subplots(figsize=(12, 8))
                plt.subplots_adjust(left=0.01, right=0.9, top=0.95, bottom=0.01)

                vmin = 0
                vmax = casos.max().max() 

                def update(frame):
                    semana = semanas[frame]
                    df = preparar_df_semana(casos, semana)
                    ax.clear()
                    df.plot(column='casos', cmap='OrRd', linewidth=0.8, ax=ax,
                        edgecolor='0.7', legend=False, vmin=vmin, vmax=vmax)
                    ax.set_xlim(bahia.total_bounds[[0, 2]])
                    ax.set_ylim(bahia.total_bounds[[1, 3]])
                    ax.axis('off')
                    ax.set_title(f'Óbitos acumulados de Covid-19 - {ano}, Semana {semana}', fontsize=15)

                sm = plt.cm.ScalarMappable(cmap='OrRd', norm=plt.Normalize(vmin=vmin, vmax=vmax))
                sm._A = []
                fig.colorbar(sm, ax=ax, orientation="vertical", shrink=0.5, label="Casos acumulados")

                ani = FuncAnimation(fig, update, frames=len(semanas), interval=300)
                ani.save(nome_arquivo, writer='pillow', fps=4)
                st.image(nome_arquivo)
                
            print(df_filtrado)
            semanas = sorted(df_filtrado.index)
            animar_mapa(df_filtrado, semanas, escolha_ano, "casos_acumulados.gif")



    if submeter and dados == "Casos":
        
        municipio_selecionado = municipios_selecionados(municipios, casos)
        municipio_selecionado["DATA DA NOTIFICACAO"] = pd.to_datetime(municipio_selecionado["DATA DA NOTIFICACAO"], errors="coerce" )
        escolha_ano_int = int(escolha_ano)
        municipio_selecionado = municipio_selecionado[municipio_selecionado["DATA DA NOTIFICACAO"].dt.year == escolha_ano_int]
            
        if agrupamento == "Semanal":
            municipio_selecionado['semanas'] = municipio_selecionado['DATA DA NOTIFICACAO'].dt.isocalendar().week
                
            df_filtrado = (
                    municipio_selecionado.groupby(['semanas', 'name_muni']).size()
                    .unstack(fill_value=0)
                    .sort_index()
                    .cumsum()
                )



            bahia = read_municipality(code_muni=29, year=2019)
            bahia['name_muni'] = bahia['name_muni'].apply(
            lambda x: unidecode(x).upper().strip() if pd.notna(x) else x
            )

            
            def preparar_df_semana(casos_semana, semana):
                df = bahia.copy()
    
                if semana in casos_semana.index:
                    casos_df = casos_semana.loc[semana].reset_index()
                    casos_df.columns = ['name_muni', 'casos'] 
        
                    df = df.merge(casos_df, on='name_muni', how='left')
                    df['casos'] = df['casos'].fillna(0)
                else:
                    df['casos'] = 0
                
                ####### colocar aqui para atualizar as taxas
                # fazer um merge entre pop e df, ai fazer a divisao no vetor
                pop.rename(columns={'População Residente - Estimativas para o TCU - Bahia': 'name_muni'}, inplace=True)
                df = pd.merge(df, pop, on='name_muni', how='left')
                #tem dois municipios com nomes diferentes 

                df['casos'] = df['casos'] / df['Unnamed: 1']
                # tem que ajustar o vmax
                return df
            
            def animar_mapa(casos, semanas, ano, nome_arquivo):
                fig, ax = plt.subplots(figsize=(12, 8))
                plt.subplots_adjust(left=0.01, right=0.9, top=0.95, bottom=0.01)

                vmin = 0
                #vmax = casos.max().max() 
                vmax = 0.13

                def update(frame):
                    semana = semanas[frame]
                    df = preparar_df_semana(casos, semana)

                    ax.clear()
                    df.plot(column='casos', cmap='OrRd', linewidth=0.8, ax=ax,
                        edgecolor='0.7', legend=False, vmin=vmin, vmax=vmax)
                    ax.set_xlim(bahia.total_bounds[[0, 2]])
                    ax.set_ylim(bahia.total_bounds[[1, 3]])
                    ax.axis('off')
                    ax.set_title(f'Taxas (casos/população) de Casos acumulados de Covid-19 - {ano}, Semana {semana}', fontsize=15)

                sm = plt.cm.ScalarMappable(cmap='OrRd', norm=plt.Normalize(vmin=vmin, vmax=vmax))
                sm._A = []
                fig.colorbar(sm, ax=ax, orientation="vertical", shrink=0.5, label="Casos acumulados")

                ani = FuncAnimation(fig, update, frames=len(semanas), interval=4000)
                ani.save(nome_arquivo, writer='pillow', fps=4)
                st.image(nome_arquivo)

            print(df_filtrado)
            semanas = sorted(df_filtrado.index)
            animar_mapa(df_filtrado, semanas, escolha_ano, "casos_acumulados.gif")

            with open("casos_acumulados.gif", "rb") as file:
                imagem = file.read()
            st.download_button(label="Baixar GIF", data=imagem, file_name="imagem.gif",
                               mime="image/gif", icon=":material/download:",type='tertiary')
            
           



    
    
elif choose == "Sobre o Autor":
    st.title("👨‍💻 SOBRE O AUTOR")
    st.write("""Olá, meu é **Joel Santana**, estudante de estatística na Universidade Federal da Bahia (UFBA) e desenvolvi este site como parte do meu projeto de **Iniciação Científica**. No qual fui orientado pela **Professora Doutora Denise Viola**, do Departamento de Estatística do **Instituto de Matemática e Estatística (IME)** da UFBA.
    \nEste projeto busca trazer mais acessibilidade e compreensão sobre a análise de dados relacionados à **COVID-19**, e foi uma oportunidade incrível de aplicar e expandir meus conhecimentos em Estatística, Ciência de Dados e Visualização Espaço-Temporal.
    \nCaso tenha alguma dúvida ou queira conversar mais sobre o projeto, estou à disposição para contato:
    \n- 📧 **E-mail**: [joeldatascience01@gmail.com](mailto:joeldatascience01@gmail.com)
    \n- 🔗 **LinkedIn**: [linkedin.com/in/joelsantana](https://www.linkedin.com/in/joel-santana-36218734b/)
                        """)
