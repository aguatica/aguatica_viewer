from flask import Flask, render_template_string
import folium
import sys
import os

# Add the project directory to the Python path
#sys.path.append(os.path.dirname(os.path.abspath(__file__)))


from aguaticaviewer.api import APIClient
'''
if __name__ == "__main__":
    # Erstelle eine Instanz des APIClients und starte den Scheduler
    api_client = APIClient(interval=30)  # Aktualisierung des Tokens alle 30 Sekunden
    api_client.start_token_scheduler()  # Starte den Token-Scheduler in einem separaten Thread

    # Hauptprogramm, das weiterläuft und auf die Daten zugreifen kann
    api_client.run()  # Führe die Hauptlogik aus

'''
app = Flask(__name__)
@app.route('/')
def index():
    start_coords = (9.9281, -84.0907)  # Coordinates for San José, Costa Rica
    folium_map = folium.Map(location=start_coords, zoom_start=13)

    tooltip = 'Click For More Info'

    logoIcon = folium.features.CustomIcon('aguatica_logo.png', icon_size=(50, 50))

    folium.Marker(location=start_coords, popup='<strong>Here are some data from measurement Point 1: ... <strong>', tooltip=tooltip, icon=logoIcon).add_to(folium_map)

    for _, row in entries_df.iterrows():
        if isinstance(row.geometry, Point):  # Check if geometry is a Point
            latitude = row.geometry.y  # Get latitude
            longitude = row.geometry.x  # Get longitude

            # Optional: Customize the popup with additional data
            #popup_text = f"<strong>Temperature: {row['13_Temperatura']}</strong><br>"
            #popup_text += f"Conductivity: {row.get('12_Conductividad', 'N/A')}<br>"
            #popup_text += f"Collected by: {row.get('1_Nombre_del_Colecto', 'Unknown')}"

        popup_text = f"""
        <table style="width:100%; border: 1px solid black; border-collapse: collapse;">
            <tr style="border: 1px solid black;">
            <th style="border: 1px solid black; padding: 8px;">Parameter</th>
            <th style="border: 1px solid black; padding: 8px;">Value</th>
            </tr>
            <tr style="border: 1px solid black;">
            <td style="border: 1px solid black; padding: 8px;"><strong>Nombre de la finca</strong></td>
            <td style="border: 1px solid black; padding: 8px;">{row.get('2_Nombre_de_la_finca', 'N/A')}</td>
            </tr>
            <tr style="border: 1px solid black;">
            <td style="border: 1px solid black; padding: 8px;"><strong>Sitio de muestreo</strong></td>
            <td style="border: 1px solid black; padding: 8px;">{row.get('3_Sitio_de_muestreo', 'N/A')}</td>
            </tr>
            <tr style="border: 1px solid black;">
            <td style="border: 1px solid black; padding: 8px;"><strong>Fecha de colecta</strong></td>
            <td style="border: 1px solid black; padding: 8px;">{row.get('4_Da_de_la_colecta', 'N/A')}</td>
            </tr>
            <tr style="border: 1px solid black;">
            <td style="border: 1px solid black; padding: 8px;"><strong>Hora de colecta</strong></td>
            <td style="border: 1px solid black; padding: 8px;">{row.get('5_Hora_de_la_colecta', 'N/A')}</td>
            </tr>
            <tr style="border: 1px solid black;">
            <td style="border: 1px solid black; padding: 8px;"><strong>Tipo de sitio</strong></td>
            <td style="border: 1px solid black; padding: 8px;">{row.get('6_Tipo_de_sitio_de_m', 'N/A')}</td>
            </tr>
            <tr style="border: 1px solid black;">
            <td style="border: 1px solid black; padding: 8px;"><strong>Tipo de Agua</strong></td>
            <td style="border: 1px solid black; padding: 8px;">{row.get('7_Tipo_de_Agua', 'N/A')}</td>
            </tr>
            <tr style="border: 1px solid black;">
            <td style="border: 1px solid black; padding: 8px;"><strong>Tipo de mediciones</strong></td>
            <td style="border: 1px solid black; padding: 8px;">{row.get('8_Tipo_de_mediciones', 'N/A')}</td>
            </tr>
            <tr style="border: 1px solid black;">
            <td style="border: 1px solid black; padding: 8px;"><strong>GPS Coordinates</strong></td>
            <td style="border: 1px solid black; padding: 8px;">{row.get('9_Coordenas_de_GPS', 'N/A')}</td>
            </tr>
            <tr style="border: 1px solid black;">
            <td style="border: 1px solid black; padding: 8px;"><strong>pH</strong></td>
            <td style="border: 1px solid black; padding: 8px;">{row.get('10_pH', 'N/A')}</td>
            </tr>
            <tr style="border: 1px solid black;">
            <td style="border: 1px solid black; padding: 8px;"><strong>Sólidos disueltos</strong></td>
            <td style="border: 1px solid black; padding: 8px;">{row.get('11_Slidos_disueltos', 'N/A')}</td>
            </tr>
            <tr style="border: 1px solid black;">
            <td style="border: 1px solid black; padding: 8px;"><strong>Conductividad</strong></td>
            <td style="border: 1px solid black; padding: 8px;">{row.get('12_Conductividad', 'N/A')}</td>
            </tr>
            <tr style="border: 1px solid black;">
            <td style="border: 1px solid black; padding: 8px;"><strong>Temperatura</strong></td>
            <td style="border: 1px solid black; padding: 8px;">{row.get('13_Temperatura', 'N/A')}</td>
            </tr>
            <tr style="border: 1px solid black;">
            <td style="border: 1px solid black; padding: 8px;"><strong>Fosfatos</strong></td>
            <td style="border: 1px solid black; padding: 8px;">{row.get('14_Fosfatos', 'N/A')}</td>
            </tr>
            <tr style="border: 1px solid black;">
            <td style="border: 1px solid black; padding: 8px;"><strong>Nitritos</strong></td>
            <td style="border: 1px solid black; padding: 8px;">{row.get('15_Nitritos', 'N/A')}</td>
            </tr>
            <tr style="border: 1px solid black;">
            <td style="border: 1px solid black; padding: 8px;"><strong>O18</strong></td>
            <td style="border: 1px solid black; padding: 8px;">{row.get('16_O18', 'N/A')}</td>
            </tr>
            <tr style="border: 1px solid black;">
            <td style="border: 1px solid black; padding: 8px;"><strong>H2</strong></td>
            <td style="border: 1px solid black; padding: 8px;">{row.get('17_H2', 'N/A')}</td>
            </tr>
            <tr style="border: 1px solid black;">
            <td style="border: 1px solid black; padding: 8px;"><strong>E. coli</strong></td>
            <td style="border: 1px solid black; padding: 8px;">{row.get('18_Ecoli', 'N/A')}</td>
            </tr>
            <tr style="border: 1px solid black;">
            <td style="border: 1px solid black; padding: 8px;"><strong>Coliformes Totales</strong></td>
            <td style="border: 1px solid black; padding: 8px;">{row.get('19_Coliformes_totale', 'N/A')}</td>
            </tr>
            <tr style="border: 1px solid black;">
            <td style="border: 1px solid black; padding: 8px;"><strong>Foto</strong></td>
            <td style="border: 1px solid black; padding: 8px;">{row.get('20_Tome_una_foto', 'N/A')}</td>
            </tr>
            <tr style="border: 1px solid black;">
            <td style="border: 1px solid black; padding: 8px;"><strong>Video</strong></td>
            <td style="border: 1px solid black; padding: 8px;">{row.get('21_Grabe_un_video_de', 'N/A')}</td>
            </tr>
            <tr style="border: 1px solid black;">
            <td style="border: 1px solid black; padding: 8px;"><strong>Notas adicionales</strong></td>
            <td style="border: 1px solid black; padding: 8px;">{row.get('22_Anote_cualquier_c', 'N/A')}</td>
            </tr>
        </table>
        """

        # Add marker to the map
        folium.Marker(
            location=(latitude, longitude),
            popup=popup_text,
            tooltip=tooltip
        ).add_to(folium_map)

    # Save the map as an HTML file in the templates directory
    folium_map.save('templates/map.html')

    # Render the map.html directly using render_template_string
    with open('templates/map.html', 'r') as f:
        map_html = f.read()

    return render_template_string(map_html)

if __name__ == '__main__':
    app.run(debug=True)  # Keep debug=True for development
