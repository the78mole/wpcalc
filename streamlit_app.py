import streamlit as st
import pandas as pd
import math
from datetime import datetime as dt
from pathlib import Path

# Set the title and favicon that appear in the Browser's tab bar.
st.set_page_config(
    page_title='Wärmepumpenrechner',
    page_icon=':fire:', # This is an emoji shortcode. Could be a URL too.
)

# Draw the actual page

# Set the title that appears at the top of the page.
'''
# :fire: Wärmepumpenrechner

Berechnung der Amortisation einer Wärmepumpe gegenüber eines neuen Gas- oder Ölkessels.

Dieses Tool ist möglichst einfach gehalten und beinhaltet auch keine prozentualen Preissteigerung der Energiekosten abseits des steigenden CO2-Preises ab 2027. Dies hat auch nur wenig Auswirkungen auf die Amortisation, da in den nächsten Jahren die Strompreise noch recht stark an die fossilen Preise gekoppelt sind.

Die Inflation ist ebenfalls nicht berücksichtigt, da sie sich auf alle Energieformen etwa gleich auswirken wird. Insgesamt verkompliziert es die Rechnung nur, hat aber keinen Mehrwert.

Möchte man erfahren, wie sich die Wärmepumpe auswirkt, wenn man die alte Heizung drin lässt, dann einfach die Kosten für den Tausch auf 0 € setzen.
'''

# Add some spacing
''
''

heizopts = { "gas" : "Erdgas", "oil" : "Heizöl EL" }

col1, col2 = st.columns(2)
col3, col4 = st.columns(2)

with col1: 
    st.write("### Altanlage")
    altheiz = st.selectbox("Heizungsart", heizopts.values())
    if altheiz == "Erdgas":
        old_gas = True
        old_oil = False
    else:
        old_oil = True
        old_gas = False

    co2intenshelp = "Die CO2-Intensitäten werden entsprechend UBA vorausgefüllt.  \nErdgas: 216 gCO2/kWh,  \nErdöl: 2680 gCO2/Liter = 268 gCO2/kWh"
    if old_gas:
        # Laut BMWK 0,65 ct/kWh @ 30 €/t_CO2
        co2gas_gperkwh = st.slider(
            "gCO2_eq pro kWh Gas", 200, 400, 216, help=co2intenshelp)
        cons_kWh = st.number_input("Gasbedarf pro Jahr (kWh)", value=30000)
        act_gasprice = st.number_input("Gaspreis aktuell (ct/kWh)", 0.0, 30.0, 11.78, 0.1)
    else:
        # bei 266 g_CO2/Liter => 7,89 ct/Liter
        co2oil_gprol = st.slider(
            "gCO2_eq pro kWh HEL", 2000, 4000, 2680, help=co2intenshelp) 
        cons_liter = st.number_input("Ölbedarf pro Jahr (l)", value=3500)
        st.write(f"Entspricht {cons_liter * 10} kWh/a")
        act_oilprice = st.slider("Heizölpreis €/Liter",0.5,2.0,1.01,0.01)
        act_oilprice_kWh = 10 * act_oilprice # recalc to ct/kWh
        cons_kWh = cons_liter * 10

    repl_price = st.number_input("Preis für Ersatz", 0, 20000, 9000)
    burn_perf = st.slider("Wirkungsgrad Kessel", 50, 110, 90)

with col2:
    st.write("### Wärmepumpe")
    wp_choice = st.selectbox("Vorauswahl für Wärmepumpendaten", ["Ein Dummy", "Anderer Dummy"])
    
    wp_cost = st.slider("Angebotspreis Wärmepumpe",5000, 50000, 40000, 100)

    tooltip_jaz = """Bitte hier eventuelle Verluste durch Pufferspeicher einrechnen"""
    wp_jaz = st.slider("Hersteller JAZ", 2.0, 8.0, 4.0, 0.1, help=tooltip_jaz)

    tooltip_incent = """TODO: Diese Auswahl füllt die nächsten Felder aus, bitte prüfen."""
    incent_choice = st.selectbox("Förderprogramm", ["keines", "BEG (normal)", "BEG (schnell)", "BEG (max)"], help=tooltip_incent)

    if incent_choice == "BEG (normal)":
        wp_incent_p = 50
    elif incent_choice == "BEG (schnell)":
        wp_incent_p = 60
    elif incent_choice == "BEG (max)":
        wp_incent_p = 70
    else:
        wp_incent_p = 0

    wp_incent = st.number_input("Förderung %", 0, 100, wp_incent_p)
    wp_incent_max = st.number_input("Förderung max. €", 0, 100000, 30000)

    if wp_cost > wp_incent_max:
        cost_red = wp_incent_max * wp_incent / 100
    else:
        cost_red = wp_cost * wp_incent / 100
    
    initial_wp = wp_cost - cost_red
    #st.write(f"Anschaffungskosten: {wp_cost:.0f} €")         
    st.markdown("Kosten abzgl. Förderung: "
                "<span style='font-size: 2em; font-weight: bold;'>"
                f"`{initial_wp:.0f}`</span> €", 
                unsafe_allow_html=True)


with col3:
    st.write("### Annahmen")
    co2price_2027 = st.slider("Erwarteter CO2-Preis €/t", 50, 1000, 250)
    elprice = st.slider("Erwarteter Strompreis ct/kWh", 20.0, 60.0, 30.0, 0.1)
    co2price_pre27 = 55
    if old_gas:
        co2_price_ct_per_EUR_gas = 1.19 * co2gas_gperkwh / 1000000
    else:
        co2_price_ct_per_EUR_oil = 1.19 * (co2oil_gprol / 10) / 1000000
    curyear = dt.now().year
    startyear = st.slider("Beginn im Jahr", curyear - 10, curyear + 10, curyear, 1)
    calclength = st.slider("Anzahl Jahre:", 5, 50, 20)

with col4:

    st.write("### Kosten")
    
    if old_gas:
        price_part_pre2027 = 100 * co2_price_ct_per_EUR_gas * co2price_pre27 
        price_part_2027 = 100 * co2_price_ct_per_EUR_gas * co2price_2027
        add_text = " (ab 2027)"
        st.write(f"CO2-Kosten (vor 2027): {co2price_pre27} €/t")
        st.write(f"CO2-Kosten {add_text}: {co2price_2027} €/t")

        st.write("CO2-Preisanteil (vor 2027): "
                f"{price_part_pre2027:.2f} ct/kWh")
        st.write(f"CO2-Preisanteil{add_text}: "
                f"{price_part_2027:.2f} ct/kWh")
        
        st.write("#### Alte Heizung")
        st.markdown(f"Wärmepreis (aktuell): "
                    "<span style='font-family: monospace;"
                    "color: orange; font-weight: bold;'>"
                    f"{100 * act_gasprice / burn_perf:.2f}</span> ct/kWh", unsafe_allow_html=True)
        totprice_gas = (act_gasprice - price_part_pre2027 +
                        price_part_2027) / burn_perf
        st.markdown(f"Wärmepreis {add_text}: "
                    "<span style='font-family: monospace;"
                    "color: red; font-weight: bold;'>"
                    f"{100 * totprice_gas:.2f}</span> ct/kWh", unsafe_allow_html=True)

        st.write("#### Wärmepumpe")
        totprice_wp = elprice / wp_jaz
        st.markdown(f"Wärmepreis: "
                    "<span style='font-family: monospace;"
                    "color: green; font-weight: bold;'>"
                    f"{totprice_wp:.2f}</span> ct/kWh", unsafe_allow_html=True)
    else: # Heizöl
        price_part_pre2027 = 100 * co2_price_ct_per_EUR_oil * co2price_pre27 
        price_part_2027 = 100 * co2_price_ct_per_EUR_oil * co2price_2027
        add_text = " (ab 2027)"
        st.write(f"CO2-Kosten (vor 2027): {co2price_pre27} €/t")
        st.write(f"CO2-Kosten {add_text}: {co2price_2027} €/t")

        st.write("CO2-Preisanteil (vor 2027): "
                f"{price_part_pre2027:.2f} ct/kWh")
        st.write(f"CO2-Preisanteil{add_text}: "
                f"{price_part_2027:.2f} ct/kWh")
        
        st.write("#### Alte Heizung")
        st.markdown(f"Wärmepreis (aktuell): "
                    "<span style='font-family: monospace;"
                    "color: orange; font-weight: bold;'>"
                    f"{100 * act_oilprice_kWh / burn_perf:.2f}</span> ct/kWh", unsafe_allow_html=True)
        totprice_oil = (act_oilprice_kWh - price_part_pre2027 +
                        price_part_2027) / burn_perf 
        st.markdown(f"Wärmepreis {add_text}: "
                    "<span style='font-family: monospace;"
                    "color: red; font-weight: bold;'>"
                    f"{100 * totprice_oil:.2f}</span> ct/kWh", unsafe_allow_html=True)

        st.write("#### Wärmepumpe")
        totprice_wp = elprice / wp_jaz
        st.markdown(f"Wärmepreis {add_text}: "
                    "<span style='font-family: monospace;"
                    "color: green; font-weight: bold;'>"
                    f"{totprice_wp:.2f}</span> ct/kWh", unsafe_allow_html=True)



if old_gas:
    cost_per_year_pre27 = cons_kWh * act_gasprice / burn_perf # ct->€=100
    cost_per_year_post27 = cons_kWh * totprice_gas
    cost_per_year_wp = cons_kWh / wp_jaz * (elprice / 100.0)
else: # old_oil
    cost_per_year_pre27 = cons_liter * act_oilprice / (burn_perf / 100)
    cost_per_year_post27 = cons_kWh * totprice_oil / (burn_perf / 100)
    cost_per_year_wp = cons_kWh / wp_jaz * (elprice / 100.0)
    

st.write("### Kosten pro Jahr")
st.markdown(f"Alte Heizung (vor 2027): "
    "<span style='font-family: monospace;"
    "color: orange; font-weight: bold;'>"
    f"{cost_per_year_pre27:.0f}</span> €", unsafe_allow_html=True)
st.markdown(f"Alte Heizung (ab 2027) : "
    "<span style='font-family: monospace;"
    "color: red; font-weight: bold;'>"
    f"{cost_per_year_post27:.0f}</span> €", unsafe_allow_html=True)
st.markdown(f"Wärmepumpe: "
    "<span style='font-family: monospace;"
    "color: green; font-weight: bold;'>"
    f"{cost_per_year_wp:.0f}</span> €", unsafe_allow_html=True)

# Datentabellen erstellen

years = []
cost_old = []
cost_new = []
sum_old : float = 0.0
sum_new : float = 0.0
tot_old = []
tot_new = []
cost_diff = []
tot_diff = []

for i in range(calclength):
    ayear = startyear + i
    years.append(ayear)
    is_pre27 = ayear < 2027
    cost_old_tmp : float = (repl_price if i == 0 else 0)
    cost_old_tmp += cost_per_year_pre27 if is_pre27 else cost_per_year_post27
    cost_new_tmp : float = ((initial_wp if i == 0 else 0) + 
        cost_per_year_wp )
    cost_old.append(round(cost_old_tmp,0))
    cost_new.append(round(cost_new_tmp,0))
    sum_old += cost_old_tmp
    sum_new += cost_new_tmp
    tot_old.append(round(sum_old,0))
    tot_new.append(round(sum_new,0))
    cost_diff.append(round(cost_old_tmp - cost_new_tmp,0))
    tot_diff.append(round(sum_old - sum_new, 0))

data = {
    "year" : [ f"{i}" for i in years ],
    #"difference" : sum_old - sum_new,
    #"cost_old" : cost_old,
    #"cost_new" : cost_new,
    f"{altheiz} Ges." : tot_old,
    "Wärmepumpe Ges." : tot_new,
    "Einsparung" : tot_diff
}

data_table = {
    "Jahr" : [ f"{i}" for i in years ],
    f"{altheiz} Kosten" : [ f"{i:.0f} €" for i in cost_old ],
    "WP Kosten" : [ f"{i:.0f} €" for i in cost_new ],
    f"{altheiz} Ges." : [ f"{i:.0f} €" for i in tot_old],
    "WP Ges." : [ f"{i:.0f} €" for i in tot_new],
    "Einsp." : [ f"{i:.0f} €" for i in cost_diff],
    "Einsp. Ges." : [ f"{i:.0f} €" for i in tot_diff]
}

df = pd.DataFrame(data)
dftab = pd.DataFrame(data_table)

#st.write(data)
st.header(f"Kostenvergleich grafisch über {calclength} Jahre", divider='gray')

st.line_chart(df, x="year", x_label="Jahr", y_label="€")

st.header(f"Kostenvergleich tabellarisch über {calclength} Jahre", divider='gray')
st.write(dftab)