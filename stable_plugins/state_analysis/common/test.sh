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

# Extrahiere die JSON-Ergebnis-URL
RESULT_URL=$(echo "$TASK_RESPONSE" | grep -oP '"href":\s*"\K[^"]+' | grep "out.json")
if [ -z "$RESULT_URL" ]; then
    echo "Fehler: Keine Ergebnis-URL für JSON gefunden!"
    exit 1
fi

echo "JSON-Ergebnis-URL gefunden: $RESULT_URL"

# Ergebnis abrufen und anzeigen
echo "Lade JSON-Ergebnisse von $RESULT_URL herunter ..."
RESULT_JSON=$(curl -s "$RESULT_URL")

echo "Berechnete JSON-Ergebnisse:"
echo "$RESULT_JSON"
echo "-------------------------"

# Ergebnis validieren und "result"-Wert extrahieren
RESULT_VALUE=$(echo "$RESULT_JSON" | grep -oP '"result":\s*\K[^}]+' | tr -d ' "')
if [ "$RESULT_VALUE" == "true" ]; then
    echo "Erfolg: Die Vektoren sind orthogonal."
elif [ "$RESULT_VALUE" == "false" ]; then
    echo "Erfolg: Die Vektoren sind nicht orthogonal."
else
    echo "Fehler: Unerwarteter Wert im Ergebnis: $RESULT_VALUE"
    exit 1
fi

echo "========================="
echo "Test erfolgreich abgeschlossen!"
echo "========================="
