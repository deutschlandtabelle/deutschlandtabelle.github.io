"""Deutschlandkarte: Umriss, Ortsverzeichnis, Verortung eines Vereins.

Der Umriss stammt aus **Natural Earth** (ne_50m_admin_0_countries), das
ausdrücklich gemeinfrei ist ("no rights reserved"). Er ist einmal in
Mercator-Projektion umgerechnet und liegt hier als fertiger SVG-Pfad --
die Seite lädt dafür nichts nach.

Verortet wird über den **Vereinsnamen**, denn Vereinsadressen liefert keine
der Quellen. "SG Flensburg-Handewitt" enthält Flensburg, "ALBA BERLIN"
enthält Berlin. Das ist eine Ableitung, keine Anschrift, und die Seite sagt
das auch. Wo der Name keinen bekannten Ort hergibt, bekommt der Verein
keinen Punkt auf der Karte -- eine geratene Position wäre schlimmer als
keine.

Zwei Fallen, für die es die Ausnahmenliste gibt:
  * Vereine ohne Ort im Namen (Schalke 04 spielt in Gelsenkirchen).
  * Gleichnamige Orte -- der Frankfurter HC kommt aus Frankfurt an der
    Oder, nicht aus Frankfurt am Main.
"""
from __future__ import annotations

import re
import unicodedata

# --- Umriss und Projektion ------------------------------------------------
# Mercator, dann auf 1000 Einheiten Breite normiert.
VIEWBOX = "0 0 1000 1359"
BREITE, HOEHE = 1000.0, 1359.0
_X0, _Y1, _SKALA = 5.8575, 66.2353, 109.1812

UMRISS = "M400.3 1319.4L381.3 1307.3L363.1 1295.7L357.0 1295.7L330.1 1298.0L329.3 1297.0L324.7 1290.3L320.5 1288.2L318.0 1289.3L316.3 1291.2L313.4 1290.9L301.4 1280.2L296.4 1278.6L289.6 1280.0L281.5 1285.8L278.0 1292.9L279.0 1297.0L283.2 1298.7L294.2 1297.5L295.8 1298.7L296.2 1301.0L295.0 1303.2L286.1 1305.1L283.5 1307.7L280.9 1308.4L279.2 1308.8L269.7 1306.0L255.6 1306.0L244.2 1311.0L226.0 1313.0L201.0 1312.0L192.0 1308.3L186.5 1306.1L182.5 1295.1L183.5 1278.9L189.5 1257.5L191.2 1241.7L188.5 1231.6L192.1 1216.5L201.8 1196.3L208.3 1174.9L211.5 1152.4L216.2 1137.7L225.5 1127.3L247.5 1098.4L249.2 1096.2L248.6 1081.7L242.7 1079.7L234.1 1075.5L212.0 1070.3L191.4 1067.0L182.1 1062.9L173.9 1051.9L168.9 1051.8L159.0 1055.7L146.6 1058.4L137.6 1056.1L131.9 1056.5L128.7 1058.5L127.2 1056.7L124.9 1047.3L120.2 1044.9L112.9 1042.7L108.3 1043.6L105.2 1048.3L100.3 1051.6L95.9 1050.5L81.9 1028.8L78.3 1023.9L77.4 1019.5L73.9 1011.4L65.6 1003.3L57.3 1000.7L53.2 1001.6L53.6 991.5L56.9 976.9L60.0 969.3L64.1 963.0L68.5 958.7L69.5 950.8L68.8 943.3L63.7 942.2L51.0 936.7L43.5 930.9L37.9 923.6L30.6 913.6L27.5 903.4L27.4 893.2L28.3 888.6L28.8 885.5L34.7 869.6L55.3 855.3L53.1 840.9L52.8 832.1L47.8 826.3L37.7 824.0L35.1 820.0L33.9 816.0L41.3 807.2L32.4 800.2L28.6 793.0L16.2 783.9L14.9 780.7L20.8 754.0L16.3 746.2L10.7 742.2L4.1 740.3L1.1 736.6L0.0 732.3L1.2 729.7L8.9 730.5L11.3 727.7L29.7 711.9L30.5 708.9L27.9 707.2L24.6 706.3L23.7 702.9L23.8 698.6L33.7 675.7L36.6 666.0L37.3 659.1L36.7 652.3L31.0 641.5L25.5 633.0L25.3 626.1L21.3 622.5L9.9 604.2L10.0 597.1L16.4 591.5L25.4 588.0L28.4 585.1L33.7 583.3L48.0 588.6L54.4 593.2L56.2 592.2L62.0 587.2L72.1 588.0L96.5 577.9L100.2 573.1L102.9 567.9L103.2 565.7L93.7 555.7L93.4 552.0L94.7 547.9L97.3 544.6L102.9 542.4L108.9 538.0L122.3 525.6L126.9 514.8L128.3 503.1L128.6 494.4L124.9 487.5L121.3 483.0L116.2 483.7L106.5 483.3L97.3 479.4L92.3 473.1L91.1 467.6L93.3 464.1L94.0 459.8L92.6 455.4L93.2 451.8L97.3 448.9L126.2 449.0L128.3 445.8L130.3 428.9L137.5 403.3L144.3 388.9L145.5 382.9L145.4 348.7L146.3 331.4L141.3 323.2L130.6 314.3L132.9 295.6L136.4 281.1L147.3 263.1L155.9 258.2L193.4 255.2L234.9 256.5L252.2 283.6L245.8 297.5L255.8 303.9L260.7 301.6L264.4 289.5L266.8 276.1L270.4 272.0L283.2 282.0L287.7 288.9L288.0 310.9L292.7 281.1L289.2 260.1L291.6 239.8L296.8 229.2L301.5 222.4L331.9 229.7L365.5 225.9L378.3 233.8L407.0 273.1L416.6 279.5L428.7 281.5L412.0 273.1L377.2 225.3L366.7 219.4L350.7 217.6L340.7 212.9L334.4 205.7L332.6 199.2L332.9 150.6L326.9 143.4L319.1 140.9L314.3 144.2L304.3 144.2L302.2 133.2L304.7 125.0L324.7 119.4L337.8 111.9L338.4 98.6L330.1 88.1L320.1 68.8L308.4 50.7L307.1 29.6L307.1 29.6L327.5 30.0L332.5 30.8L363.4 40.7L370.9 47.6L380.4 48.0L397.6 41.5L410.3 38.7L415.3 42.7L422.3 44.3L423.9 44.3L424.5 47.8L440.5 52.8L447.2 60.8L454.7 73.0L455.4 90.5L445.9 103.0L437.9 111.0L467.9 108.0L470.9 115.1L475.5 122.9L491.6 117.4L532.2 140.2L556.7 129.1L562.9 128.5L568.5 146.9L562.4 165.5L540.8 185.2L545.6 197.4L552.5 200.1L572.8 197.5L605.1 209.5L611.8 205.8L638.0 178.1L648.4 172.2L682.8 167.9L689.1 157.1L703.0 146.3L712.0 134.5L733.5 111.9L755.7 116.0L768.7 120.3L782.9 122.5L795.9 146.5L828.7 173.0L858.9 170.7L869.6 195.7L874.3 226.4L883.6 236.0L891.7 242.3L916.3 248.9L917.3 249.3L918.1 253.4L919.6 268.6L921.6 281.2L934.3 331.2L934.0 343.4L933.9 346.6L929.2 363.6L921.0 377.9L910.1 386.0L904.2 395.0L903.0 404.8L916.7 422.1L945.1 446.8L956.6 467.9L951.2 485.3L949.6 498.1L951.7 506.2L956.2 512.8L963.2 517.7L966.0 525.3L964.6 535.5L965.9 542.6L971.2 547.6L970.7 549.6L968.1 556.7L964.7 569.6L962.7 579.0L954.7 591.8L957.1 602.7L963.4 615.5L968.2 621.9L969.7 628.0L966.6 642.4L968.1 646.1L987.9 656.7L991.2 661.6L993.1 671.8L1000.0 693.6L994.2 721.0L989.2 736.0L977.9 759.8L977.4 762.0L976.1 764.8L972.7 769.0L968.0 769.6L960.9 766.5L956.0 762.6L957.1 752.3L954.0 751.6L950.1 745.4L948.6 738.6L944.4 735.8L929.1 733.0L923.9 731.0L919.9 732.4L916.9 737.2L918.8 741.5L921.7 745.8L930.2 752.4L929.3 755.1L911.0 761.6L899.5 768.2L888.8 772.0L877.9 778.8L856.4 786.6L840.6 788.6L837.3 790.7L831.4 803.7L827.4 806.5L823.6 805.0L820.7 802.9L817.1 804.7L813.2 809.0L809.3 810.7L805.8 810.6L799.6 822.0L781.6 825.5L779.5 831.4L776.2 838.2L773.6 839.9L765.4 837.2L754.2 835.7L747.8 839.4L740.0 841.5L730.6 842.1L720.1 849.6L709.8 862.6L704.0 874.2L700.9 878.3L695.9 867.5L689.7 860.1L685.4 856.2L681.5 856.2L680.5 857.8L680.4 863.4L684.6 872.9L689.8 879.3L690.6 884.0L693.3 892.6L700.8 902.0L712.6 909.4L720.6 916.7L726.5 926.9L726.6 930.0L725.0 934.1L722.2 938.0L719.8 943.1L713.3 953.3L715.2 957.8L720.5 963.4L725.3 970.2L731.3 981.1L739.6 1000.2L745.0 1008.0L752.3 1016.1L759.4 1022.3L770.7 1022.1L782.4 1033.9L795.2 1050.9L804.7 1058.7L811.4 1061.1L816.8 1067.2L821.7 1076.0L823.6 1081.0L827.9 1084.7L839.6 1084.0L854.6 1097.8L863.9 1107.9L868.8 1116.0L867.5 1119.2L866.9 1129.3L867.0 1140.0L865.6 1145.7L858.9 1153.1L855.4 1154.7L853.5 1156.3L833.0 1146.6L831.3 1148.3L830.0 1149.5L824.5 1177.5L820.7 1182.9L815.1 1187.9L803.3 1192.7L795.2 1194.7L788.8 1197.1L768.6 1208.8L759.5 1215.8L753.7 1224.6L753.6 1229.7L763.4 1244.6L774.7 1259.9L774.8 1273.4L769.8 1283.5L768.7 1287.4L772.0 1288.8L778.2 1289.4L783.5 1291.1L785.7 1298.2L785.1 1310.5L783.3 1322.0L781.4 1326.8L776.3 1327.2L766.6 1322.2L759.0 1316.5L756.1 1312.9L755.9 1308.7L757.6 1306.0L754.9 1300.7L745.5 1295.9L735.5 1298.0L728.1 1301.3L723.4 1301.1L718.2 1296.4L710.3 1292.8L699.9 1290.5L693.5 1287.9L692.1 1289.4L692.9 1299.5L690.9 1303.9L639.7 1309.8L624.1 1315.2L612.8 1322.3L604.4 1325.4L602.3 1329.7L594.0 1335.4L584.6 1337.2L582.3 1335.4L576.3 1338.0L566.0 1340.5L559.4 1339.7L556.2 1335.1L549.9 1328.1L547.3 1323.2L547.6 1320.0L533.3 1319.4L524.2 1315.7L505.0 1316.5L500.3 1314.9L499.3 1316.6L496.4 1336.7L492.6 1344.9L486.4 1353.4L478.6 1358.1L472.3 1359.0L472.6 1352.8L474.1 1345.3L469.6 1343.6L462.8 1342.7L459.5 1340.5L460.4 1334.8L458.8 1331.5L456.0 1327.6L449.2 1322.4L434.7 1314.8L424.9 1311.1L421.2 1315.1L414.1 1319.1L403.0 1317.8L400.3 1319.4ZM857.3 127.8L860.0 140.4L857.1 146.8L844.8 136.1L832.5 136.3L825.1 152.7L819.6 153.4L800.6 138.5L797.5 131.2L796.9 125.1L799.6 104.1L799.1 97.5L805.1 90.2L806.0 79.7L816.6 68.6L826.0 68.2L829.0 77.6L833.5 84.1L849.3 91.3L851.6 94.6L853.1 99.1L845.7 108.0L843.2 112.6L845.5 119.8L857.3 127.8ZM912.1 208.4L910.7 214.2L912.3 223.2L907.8 222.5L894.3 224.6L880.9 221.7L878.3 210.5L880.5 199.8L875.1 192.5L870.1 188.1L869.4 182.0L870.2 175.5L893.2 192.8L912.1 208.4ZM592.3 121.2L575.6 121.6L569.2 114.0L562.7 112.1L566.2 102.9L570.7 99.5L587.0 105.5L592.1 117.4L592.3 121.2ZM267.5 51.6L265.0 55.4L266.2 28.6L278.2 0.0L283.2 0.6L278.0 8.4L276.5 13.8L274.4 24.6L275.4 30.2L302.7 31.8L299.5 36.8L271.8 40.1L267.5 51.6ZM298.1 65.7L293.9 70.3L283.5 69.8L277.6 65.4L279.5 60.8L285.0 57.2L289.6 56.7L296.5 58.9L298.1 65.7Z"


def projizieren(lat: float, lon: float) -> tuple[float, float]:
    """Grad in Karten-Einheiten. Gleiche Rechnung wie für den Umriss."""
    import math
    my = math.degrees(math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)))
    return (round((lon - _X0) * _SKALA, 1), round((_Y1 - my) * _SKALA, 1))


# --- Ortsverzeichnis ------------------------------------------------------
# Städte, die Vereine der überregionalen Ligen stellen, dazu die großen
# Städte des Landes. Das Verzeichnis muss nicht vollständig sein: was fehlt,
# bekommt keinen Punkt, und das ist das gewünschte Verhalten.
ORTE: dict[str, tuple[float, float]] = {
    "Berlin": (52.52, 13.40), "Hamburg": (53.55, 9.99), "München": (48.14, 11.58),
    "Köln": (50.94, 6.96), "Frankfurt": (50.11, 8.68), "Stuttgart": (48.78, 9.18),
    "Düsseldorf": (51.23, 6.78), "Dortmund": (51.51, 7.47), "Essen": (51.46, 7.01),
    "Leipzig": (51.34, 12.37), "Bremen": (53.08, 8.81), "Dresden": (51.05, 13.74),
    "Hannover": (52.37, 9.73), "Nürnberg": (49.45, 11.08), "Duisburg": (51.43, 6.76),
    "Bochum": (51.48, 7.22), "Wuppertal": (51.26, 7.15), "Bielefeld": (52.02, 8.53),
    "Bonn": (50.73, 7.10), "Münster": (51.96, 7.63), "Karlsruhe": (49.01, 8.40),
    "Mannheim": (49.49, 8.47), "Augsburg": (48.37, 10.90), "Wiesbaden": (50.08, 8.24),
    "Mönchengladbach": (51.19, 6.44), "Gelsenkirchen": (51.52, 7.10),
    "Braunschweig": (52.27, 10.52), "Chemnitz": (50.83, 12.92), "Kiel": (54.32, 10.14),
    "Aachen": (50.78, 6.08), "Halle": (51.48, 11.97), "Magdeburg": (52.13, 11.63),
    "Freiburg": (47.99, 7.85), "Krefeld": (51.33, 6.56), "Lübeck": (53.87, 10.69),
    "Oberhausen": (51.47, 6.85), "Erfurt": (50.98, 11.03), "Mainz": (50.00, 8.27),
    "Rostock": (54.09, 12.14), "Kassel": (51.31, 9.49), "Hagen": (51.36, 7.47),
    "Saarbrücken": (49.24, 6.99), "Hamm": (51.68, 7.82), "Potsdam": (52.40, 13.06),
    "Ludwigshafen": (49.48, 8.44), "Oldenburg": (53.14, 8.21),
    "Leverkusen": (51.03, 7.00), "Osnabrück": (52.28, 8.05), "Solingen": (51.17, 7.08),
    "Heidelberg": (49.40, 8.69), "Darmstadt": (49.87, 8.65), "Paderborn": (51.72, 8.75),
    "Regensburg": (49.02, 12.10), "Ingolstadt": (48.77, 11.43), "Würzburg": (49.79, 9.94),
    "Wolfsburg": (52.42, 10.79), "Ulm": (48.40, 9.99), "Heilbronn": (49.14, 9.22),
    "Pforzheim": (48.89, 8.70), "Göttingen": (51.53, 9.94), "Bottrop": (51.52, 6.93),
    "Trier": (49.75, 6.64), "Recklinghausen": (51.61, 7.20), "Reutlingen": (48.49, 9.21),
    "Bremerhaven": (53.55, 8.58), "Koblenz": (50.36, 7.59), "Jena": (50.93, 11.59),
    "Remscheid": (51.18, 7.19), "Erlangen": (49.60, 11.00), "Moers": (51.45, 6.63),
    "Siegen": (50.87, 8.02), "Hildesheim": (52.15, 9.95), "Salzgitter": (52.15, 10.33),
    "Cottbus": (51.76, 14.33), "Kaiserslautern": (49.44, 7.77), "Gütersloh": (51.91, 8.39),
    "Schwerin": (53.63, 11.41), "Witten": (51.44, 7.34), "Gera": (50.88, 12.08),
    "Iserlohn": (51.37, 7.70), "Zwickau": (50.72, 12.49), "Düren": (50.80, 6.48),
    "Lünen": (51.62, 7.53), "Flensburg": (54.78, 9.44), "Konstanz": (47.66, 9.18),
    "Worms": (49.63, 8.37), "Marburg": (50.81, 8.77), "Dessau": (51.83, 12.24),
    "Gießen": (50.58, 8.68), "Ludwigsburg": (48.90, 9.19), "Offenburg": (48.47, 7.94),
    "Rosenheim": (47.86, 12.13), "Landshut": (48.54, 12.15), "Bamberg": (49.89, 10.89),
    "Bayreuth": (49.95, 11.58), "Aschaffenburg": (49.98, 9.15), "Lüneburg": (53.25, 10.41),
    "Celle": (52.62, 10.08), "Minden": (52.29, 8.92), "Fulda": (50.55, 9.68),
    "Neubrandenburg": (53.56, 13.26), "Görlitz": (51.15, 14.99),
    "Stralsund": (54.31, 13.09), "Greifswald": (54.09, 13.38), "Emden": (53.37, 7.21),
    "Wilhelmshaven": (53.53, 8.11), "Delmenhorst": (53.05, 8.63), "Hameln": (52.10, 9.36),
    "Nordhorn": (52.43, 7.07), "Elmshorn": (53.75, 9.65), "Norderstedt": (53.71, 9.98),
    "Coburg": (50.26, 10.96), "Schweinfurt": (50.05, 10.23), "Hof": (50.31, 11.92),
    "Passau": (48.57, 13.46), "Kempten": (47.73, 10.31), "Memmingen": (47.98, 10.18),
    "Friedrichshafen": (47.65, 9.48), "Tübingen": (48.52, 9.05), "Esslingen": (48.74, 9.31),
    "Göppingen": (48.70, 9.65), "Balingen": (48.28, 8.85), "Lemgo": (52.03, 8.90),
    "Melsungen": (51.13, 9.55), "Wetzlar": (50.55, 8.50), "Eisenach": (50.98, 10.32),
    "Gummersbach": (51.03, 7.57), "Bietigheim": (48.95, 9.13), "Nordhausen": (51.50, 10.79),
    "Dormagen": (51.10, 6.84), "Hüttenberg": (50.53, 8.58), "Emsdetten": (52.17, 7.53),
    "Ahlen": (51.76, 7.89), "Coesfeld": (51.95, 7.17), "Rimpar": (49.86, 9.95),
    "Vechta": (52.73, 8.29), "Crailsheim": (49.13, 10.07), "Weißenfels": (51.20, 11.97),
    "Meppen": (52.69, 7.29), "Buxtehude": (53.47, 9.70), "Blomberg": (51.94, 9.09),
    "Neckarsulm": (49.19, 9.23), "Metzingen": (48.54, 9.28), "Buchholz": (53.33, 9.88),
    "Elversberg": (49.32, 7.13), "Sinsheim": (49.25, 8.88), "Sandhausen": (49.34, 8.66),
    "Verl": (51.88, 8.52), "Unterhaching": (48.07, 11.62), "Wehen": (50.14, 8.27),
    "Aalen": (48.84, 10.09), "Weiden": (49.68, 12.16), "Frankfurt (Oder)": (52.35, 14.55),
    "Bad Langensalza": (51.11, 10.65), "Zweibrücken": (49.25, 7.36),
    "Bergisch Gladbach": (50.99, 7.13), "Herzogenaurach": (49.57, 10.89),
    "Lippstadt": (51.67, 8.35), "Rödinghausen": (52.24, 8.50), "Homburg": (49.33, 7.34),
    "Rehden": (52.61, 8.49), "Straelen": (51.44, 6.27), "Oberachern": (48.63, 8.08),
    "Speyer": (49.32, 8.43), "Schifferstadt": (49.39, 8.38), "Kandel": (49.08, 8.19),
    "Landau": (49.20, 8.12), "Pirmasens": (49.20, 7.60), "Neuwied": (50.43, 7.47),
    "Bad Kreuznach": (49.84, 7.87), "Idar-Oberstein": (49.71, 7.31),
    "Gießen": (50.58, 8.68), "Herne": (51.54, 7.22), "Castrop-Rauxel": (51.55, 7.31),
    "Gladbeck": (51.57, 6.99), "Marl": (51.66, 7.09), "Dorsten": (51.66, 6.96),
    "Arnsberg": (51.40, 8.06), "Soest": (51.57, 8.11), "Detmold": (51.94, 8.88),
    "Herford": (52.12, 8.67), "Rheine": (52.28, 7.44), "Bocholt": (51.84, 6.61),
    "Velbert": (51.34, 7.04), "Neuss": (51.20, 6.69), "Viersen": (51.26, 6.39),
    "Wesel": (51.66, 6.62), "Kleve": (51.79, 6.14), "Euskirchen": (50.66, 6.79),
    "Wolfenbüttel": (52.16, 10.54),
}

# Wenn weder Vereins- noch Ligenname einen Ort hergeben, bleibt das
# Verbandsgebiet. Das ist eine grobe Verortung und wird auf der Seite auch
# als solche ausgewiesen -- aber besser, als den Verein wegzulassen.
# Längere Schlüssel gewinnen: "Rheinland-Pfalz" vor "Rheinland".
GEBIETE: dict[str, tuple[float, float]] = {
    "westfalen": (51.75, 8.10), "niederrhein": (51.40, 6.60),
    "mittelrhein": (50.80, 7.00), "rheinland-pfalz": (49.90, 7.60),
    "rheinhessen": (49.75, 8.15), "rheinland": (50.35, 7.50),
    "südwest": (49.40, 7.80), "saarland": (49.38, 7.02), "saar": (49.38, 7.02),
    "südbaden": (47.95, 7.95), "baden": (49.10, 8.60),
    "württemberg": (48.70, 9.40), "bayern": (48.90, 11.40),
    "hessen": (50.60, 9.00), "niedersachsen": (52.70, 9.50),
    "bremen": (53.08, 8.81), "hamburg": (53.55, 9.99),
    "schleswig-holstein": (54.20, 9.70), "mecklenburg": (53.70, 12.40),
    "brandenburg": (52.40, 13.00), "berlin": (52.52, 13.40),
    "sachsen-anhalt": (51.95, 11.70), "sachsen": (51.10, 13.30),
    "thüringen": (50.90, 11.00), "handballregion-nord": (53.80, 10.00),
    "nordrhein-westfalen": (51.45, 7.20), "nrw": (51.45, 7.20),
    "oldenburg": (53.14, 8.21), "hannover": (52.37, 9.73),
    "pfalz": (49.40, 8.00), "franken": (49.60, 10.80), "schwaben": (48.40, 10.50),
    "oberbayern": (48.20, 11.60), "niederbayern": (48.60, 12.60),
    "oberpfalz": (49.40, 12.00),
}
_GEBIETE_SORTIERT = sorted(GEBIETE, key=len, reverse=True)

# Vereine, deren Name den Ort nicht oder falsch nennt. Ohne diese Liste
# landet der Frankfurter HC 500 km zu weit westlich.
AUSNAHMEN: dict[str, str] = {
    "frankfurter hc": "Frankfurt (Oder)",
    "schalke": "Gelsenkirchen",
    "st. pauli": "Hamburg",
    "st pauli": "Hamburg",
    "hertha": "Berlin",
    "hoffenheim": "Sinsheim",
    "rhein-neckar löwen": "Mannheim",
    "bergischer hc": "Wuppertal",
    "thüringer hc": "Bad Langensalza",
    "syntainics mbc": "Weißenfels",
    "mitteldeutscher bc": "Weißenfels",
    "fc bayern": "München",
    "borussia mönchengladbach": "Mönchengladbach",
    "vfl bochum": "Bochum",
    "sv sandhausen": "Sandhausen",
    "sv wehen": "Wiesbaden",
    "spvgg unterhaching": "Unterhaching",
    "viktoria köln": "Köln",
    "energie cottbus": "Cottbus",
    "hansa rostock": "Rostock",
    "dynamo dresden": "Dresden",
    "carl zeiss jena": "Jena",
    "turbine potsdam": "Potsdam",
    "eintracht braunschweig": "Braunschweig",
    "arminia bielefeld": "Bielefeld",
    "alemannia aachen": "Aachen",
    "waldhof mannheim": "Mannheim",
    "rot-weiss essen": "Essen",
    "preußen münster": "Münster",
    "erzgebirge aue": "Zwickau",
}

_WORT = re.compile(r"[^\wäöüß]+", re.I)


def _normal(text: str) -> str:
    text = unicodedata.normalize("NFC", str(text or "")).lower()
    return " " + _WORT.sub(" ", text).strip() + " "


# Längere Ortsnamen zuerst prüfen: "Frankfurt (Oder)" vor "Frankfurt",
# "Bergisch Gladbach" vor "Gladbach".
_SORTIERT = sorted(ORTE, key=len, reverse=True)


def _treffer(name: str) -> tuple[str, float, float] | None:
    """Ersten bekannten Ort in einem Text finden."""
    text = _normal(name)
    for muster, ort in AUSNAHMEN.items():
        if " " + muster + " " in text or text.strip().endswith(muster):
            lat, lon = ORTE[ort]
            return (ort, *projizieren(lat, lon))
    for ort in _SORTIERT:
        if " " + _normal(ort).strip() + " " in text:
            lat, lon = ORTE[ort]
            return (ort, *projizieren(lat, lon))
    return None


def verorten(verein: str, liga: str = "", gebiet: str = "") -> dict | None:
    """Wo sitzt dieser Verein -- und wie sicher ist das?

    Drei Anläufe, vom Genauen zum Groben:
      1. der Vereinsname ("SG Flensburg-Handewitt"),
      2. der Ligenname ("A-Klasse Koblenz Herren Gruppe 1"),
      3. das Verbandsgebiet ("Rheinland-Pfalz").

    `art` sagt, welcher davon getroffen hat. Die Seite weist damit aus, wo
    der Punkt genau sitzt und wo er nur die Gegend angibt.
    """
    for text, art in ((verein, "verein"), (liga, "liga")):
        fund = _treffer(text or "")
        if fund:
            return {"ort": fund[0], "x": fund[1], "y": fund[2], "art": art}
    # Bindestriche und Punkte sind im Verbandsnamen mal da, mal nicht
    # ("Handballregion-Nord", "Handballregion Nord") -- beide Seiten werden
    # deshalb gleich behandelt.
    raum = _normal(gebiet)
    for schluessel in _GEBIETE_SORTIERT:
        if _normal(schluessel).strip() in raum:
            lat, lon = GEBIETE[schluessel]
            x, y = projizieren(lat, lon)
            return {"ort": (gebiet or "").strip(), "x": x, "y": y, "art": "gebiet"}
    return None
