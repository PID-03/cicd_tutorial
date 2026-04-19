import requests
from bs4 import BeautifulSoup
import json
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)

logger = logging.getLogger(__name__)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ],
    force=True
)

def fetch_rainfall_density(lat, lon):
    url = "https://www.bom.gov.au/water/designRainfalls/revised-ifd/?"
    
    params={
        "coordinate_type":"dd",
        "latitude":lat,
        "longitude":lon,
        "design":"ifds",
        "sdmin":"true",
        "sdhr":"true",
        "sdday":"true"
    }
    headers={
        "User-Agent": "Mozilla/5.0"
    }

    print("Sending request to the BOM")
    logger.info("Sending request to the BOM")
    response = requests.get(url, params=params, headers=headers)

    if response.status_code != 200:
        logger.error("failed to fetch the data")
        return {"error":"Failed to fetch the data"}

    
    print("Status code:", response.status_code)
    soup = BeautifulSoup(response.text, "html.parser")

    intensity_table = soup.find("table", {"id":"intensities"})

    if not intensity_table:
        logger.error("Intensity table not found")
        return {"error":"Intensity table not found"}
  

    rows = intensity_table.find_all("tr")
    header_row = None

    for row in rows:
        if "Duration" in row.get_text():
            header_row=row
            break
    if not header_row:
        logger.error("Header row not found")
        return{"error":"Header row not found"}

    headers = header_row.find_all("th")

    probabilities  = [h.get_text(strip=True) for h in headers[1:]]
    print("probabilities",probabilities)

    rainfall_data=[]

    for row in rows[2:]:
        duration_cell = row.find("th")
        value_cells = row.find_all("td")

        if duration_cell:

            print("DURATION:", duration_cell.get_text(strip=True))

        if not duration_cell or not value_cells:
            continue

        
        duration = duration_cell.get_text(strip=True)

        
        values ={}

            
        for probe, cell in zip(probabilities, value_cells):
            probe_text = probe.replace("%","").replace("#","").replace("*","")
            if "." in probe_text:
                probe_text=probe_text.split(".")[0]
            values[probe_text]=cell.get_text(strip=True)
            
        rainfall_data.append({
            "duration_minutes":duration,
            "values_mm_per_hr":values
        })

    return rainfall_data

   



