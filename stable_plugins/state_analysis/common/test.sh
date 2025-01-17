#!/bin/bash

# URLs und Parameter
API_URL="http://localhost:5005/plugins/orthogonality_classical@v0-0-1/process/"
BASE_URL="http://localhost:5005"
DATA="vectors=[[[5.0, 0.0], [0.0, 0.0]], [[0.0, 0.0], [0.0, 1.0]]]&tolerance=0"

echo "========================="
echo "Starte Test für die API"
echo "========================="

# Sende die POST-Anfrage und extrahiere die Weiterleitungs-URL
echo "Sende POST-Anfrage an $API_URL ..."
RESPONSE=$(curl -s -i -X POST "$API_URL" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    --data "$DATA")

echo "Antwort von der API:"
echo "$RESPONSE"
echo "-------------------------"

# Extrahiere die Weiterleitungs-URL
TASK_PATH=$(echo "$RESPONSE" | grep -i "Location:" | awk '{print $2}' | tr -d '\r\n')
TASK_URL="${BASE_URL}${TASK_PATH}"

if [ -z "$TASK_PATH" ]; then
    echo "Fehler: Keine Weiterleitungs-URL erhalten!"
    exit 1
fi

echo "Prozess erfolgreich gestartet. Weiterleitungs-URL: $TASK_URL"

# Warte kurz, bevor der Status abgefragt wird
echo "Warte 2 Sekunden, bevor die Ergebnisse abgerufen werden ..."
sleep 2

# Abrufen des Task-Status
echo "Rufe Task-Status von $TASK_URL ab ..."
TASK_RESPONSE=$(curl -s "$TASK_URL")

echo "Antwort des Tasks:"
echo "$TASK_RESPONSE"
echo "-------------------------"

# Extrahiere die Ergebnis-URL aus der Antwort
RESULT_URL=$(echo "$TASK_RESPONSE" | grep -oP '"href":\s*"\K[^"]+' | grep "/files/")
if [ -z "$RESULT_URL" ]; then
    echo "Fehler: Keine Ergebnis-URL gefunden!"
    exit 1
fi

# Vollständige Ergebnis-URL
FULL_RESULT_URL="${RESULT_URL}"
echo "Ergebnis-URL gefunden: $FULL_RESULT_URL"

# Ergebnisdatei herunterladen und anzeigen
echo "Lade Ergebnisse von $FULL_RESULT_URL herunter ..."
curl -s "$FULL_RESULT_URL" -o out.txt

echo "Berechnete Ergebnisse (aus 'out.txt'):"
cat out.txt

echo "========================="
echo "Test abgeschlossen!"
echo "========================="
