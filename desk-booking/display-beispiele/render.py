"""Illustrative screen reconstructions, NOT captured device frames."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import html, json, zipfile

OUT=Path(__file__).parent
ROOT=OUT.parent.parent
S=2
CYAN='#00d2ff'; GREEN='#36ff7f'; RED='#ff3b30'; YELLOW='#ffd43b'; WHITE='#ffffff'; MUTED='#a9bbc9'
FONT=Path('C:/Windows/Fonts/segoeui.ttf')
BOLD=Path('C:/Windows/Fonts/segoeuib.ttf')
def font(n,bold=False):return ImageFont.truetype(str(BOLD if bold else FONT),int(n*S))
def text(im,x,y,t,n=20,color=WHITE,bold=False):
    ImageDraw.Draw(im).text((x*S,y*S),t,font=font(n,bold),fill=color,anchor='mm')
def box(im,xy,fill,outline=None,r=12,w=2):
    ImageDraw.Draw(im).rounded_rectangle(tuple(int(v*S) for v in xy),radius=r*S,fill=fill,outline=outline,width=w*S)
def line(im,xy,color=WHITE,w=2):ImageDraw.Draw(im).line(tuple(v*S for v in xy),fill=color,width=w*S)
def icon(im,x,y,kind,color=WHITE):
    d=ImageDraw.Draw(im)
    if kind in ('desk','height'):
        line(im,[x-12,y-4,x+12,y-4],color,3);line(im,[x-9,y-4,x-9,y+12],color);line(im,[x+9,y-4,x+9,y+12],color)
        if kind=='height':line(im,[x,y-18,x,y-8],color);line(im,[x-4,y-14,x,y-18,x+4,y-14],color)
    elif kind=='light':
        d.ellipse(((x-9)*S,(y-13)*S,(x+9)*S,(y+5)*S),outline=color,width=2*S);line(im,[x-5,y+7,x+5,y+7],color);line(im,[x-4,y+11,x+4,y+11],color)
    elif kind=='cover':
        for k in range(-12,13,6):line(im,[x-12,y+k,x+12,y+k],color)
        line(im,[x+14,y-14,x+14,y+15],color)
    elif kind=='power':
        d.arc(((x-12)*S,(y-12)*S,(x+12)*S,(y+12)*S),-55,235,fill=color,width=3*S);line(im,[x,y-16,x,y],color,3)
def base():
    im=Image.new('RGB',(480*S,480*S),'#101820')
    bg=Image.open(ROOT/'assets/your-admins-dark-background-esphome.png').convert('RGB').resize(im.size)
    im.paste(bg)
    return im
def ring(im,color,animated=False):
    d=ImageDraw.Draw(im); b=(9*S,9*S,471*S,471*S)
    if animated:
        d.ellipse(b,outline='#3d2930',width=24*S);d.arc(b,-60,30,fill=color,width=24*S)
    else:d.ellipse(b,outline=color,width=10*S)
def nav(im,selected=0,selecting=False):
    for i,k in enumerate(['desk','light','height','cover','power']):
        x=120+i*60
        box(im,(x-27,369,x+27,421),'#101820',('#999999' if selecting else CYAN) if i==selected else None,r=14,w=3)
        icon(im,x,395,k)
def arc(im,value,lo=0,hi=100):
    d=ImageDraw.Draw(im); b=(20*S,20*S,460*S,460*S)
    d.arc(b,135,405,fill='#263746',width=12*S)
    d.arc(b,135,135+270*(value-lo)/(hi-lo),fill=CYAN,width=12*S)
def booking(status='FREI',color=GREEN,person='',when='Keine weitere Buchung (365 Tage)',who='',hint='Check-in in Home Assistant',border=True,header=False,planned=False):
    im=base()
    if border:ring(im,color)
    if header:text(im,240,62,person,20)
    text(im,240,100,'your-admins',22,CYAN)
    text(im,240,146,'Schreibtisch 1',22)
    text(im,240,205,status,28,color,True)
    text(im,240,248,person,22)
    text(im,240,282,hint,16,MUTED)
    text(im,240,317,when,18,YELLOW)
    if not planned:text(im,240,345,who,20)
    nav(im)
    return im
def message(body,color=None):
    im=Image.new('RGB',(480*S,480*S),'#101820')
    if color:ring(im,color,True)
    text(im,240,76,'NACHRICHT',28,CYAN)
    import textwrap
    lines=textwrap.wrap(body,29)
    for i,t in enumerate(lines):text(im,240,190+i*29,t,20)
    box(im,(150,369,330,421),'#007f9e',r=26)
    text(im,240,395,'OK (15)',20)
    return im
def lighting(value=65,selected=0):
    im=base();arc(im,value);text(im,240,100,'your-admins',22,CYAN)
    text(im,240,155,['Deckenlicht','Schreibtischlampe','LED-Band','Stehlampe'][selected],23)
    text(im,240,230,f'{value} %',40)
    box(im,(122,258,234,302),'#165c3a');text(im,178,280,'Ein')
    box(im,(246,258,358,302),'#343e48');text(im,302,280,'Aus')
    for j in range(4):
        x=156+j*56;box(im,(x-24,317,x+24,363),'#143746',CYAN if selected==j else None);icon(im,x,340,'light')
    nav(im,1);return im
def height(value=74,selecting=False):
    im=base();arc(im,value,62,128);text(im,240,100,'your-admins',22,CYAN);text(im,240,155,'HOEHE')
    text(im,240,230,f'{value} cm',40)
    for x,t in [(182,'74 cm'),(298,'110 cm')]:
        box(im,(x-50,268,x+50,342),'#143746','#007f9e',r=16,w=1);icon(im,x,290,'desk' if x==182 else 'height');text(im,x,326,t,16)
    nav(im,2,selecting);return im
def cover(tilt=True):
    im=base();text(im,240,112,'Jalousie Fenster',22)
    for x,t in [(175,'Höhe'),(305,'Lamellen')]:
        if tilt or t=='Höhe':box(im,(x-60,139,x+60,171),'#143746');text(im,x,155,t,17)
    text(im,240,190,'Höhe: 60 %',22)
    box(im,(115,217,365,233),'#263746',r=8);box(im,(115,217,265,233),CYAN,r=8)
    if tilt:
        text(im,240,285,'Lamellen: 35 %',20);box(im,(115,312,365,328),'#263746',r=8);box(im,(115,312,202,328),CYAN,r=8)
    nav(im,3);return im
def switch(on=True):
    im=base();text(im,240,112,'Steckdose Monitor',22);icon(im,240,170,'power',CYAN if on else MUTED)
    text(im,240,220,'Ein' if on else 'Aus',22)
    for x,t,c in [(175,'Ein','#165c3a'),(305,'Aus','#343e48')]:box(im,(x-57,263,x+57,318),c);text(im,x,290,t)
    nav(im,4);return im
screens=[]
def add(title,desc,im,section='Aktueller Funktionsstand'):
    i=len(screens)+1;name=f'{i:02d}.png'
    # Round panel and explicit non-capture label on every exported example.
    mask=Image.new('L',im.size,0);ImageDraw.Draw(mask).ellipse((0,0,480*S-1,480*S-1),fill=255)
    panel=Image.new('RGB',im.size,'#080c12');panel.paste(im,(0,0),mask)
    canvas=Image.new('RGB',(520*S,590*S),'#080c12');canvas.paste(panel,(20*S,12*S))
    text(canvas,260,515,f'{i:02d} · {title}',21,WHITE,True)
    text(canvas,260,549,'ENTWURF · noch nicht umgesetzt' if section=='Geplant' else 'NACHBILDUNG · kein Geräte-Screenshot',13,CYAN)
    canvas.resize((1040,1180),Image.Resampling.LANCZOS).save(OUT/name)
    screens.append(dict(file=name,title=title,description=desc,section=section))

add('Frei','Keine aktuelle oder in weniger als 60 Minuten beginnende Reservierung. Statischer grüner Ring.',booking())
add('Spätere Reservierung','Beispiel einer Reservierung in weniger als zwei Stunden, aber mindestens 60 Minuten: Tisch bleibt frei.',booking(when='In 95 Minuten',who='Alex Beispiel'))
add('Reservierung beginnt bald','Weniger als 60 Minuten bis zum Beginn: gelber Text und statischer gelber Ring.',booking('RESERVIERT',YELLOW,when='In 25 Minuten',who='Alex Beispiel',hint='Reservierung beginnt bald'))
add('Reservierung läuft','Laufende Reservierung ohne Check-in: roter Text und statischer roter Ring.',booking('RESERVIERT',RED,when='Reserviert bis 16.11. 12:00',who='Alex Beispiel',hint='Reservierung laeuft'))
add('Eingecheckt ohne Reservierung','Aktueller Stand: weißer Check-in-Text, kein Ring und zusätzlicher Name am oberen Rand.',booking('EINGECHECKT',WHITE,'Alex Beispiel',hint='Dein Arbeitsplatz',border=False,header=True))
add('Check-in + laufende Buchung','Aktueller, von dir beanstandeter Zustand: Reservierung überschreibt den Check-in-Text; Namen erscheinen mehrfach.',booking('RESERVIERT',RED,'Alex Beispiel',when='Reserviert bis 16.11. 12:00',who='Alex Beispiel',hint='Reservierung laeuft',header=True))
add('Check-in wird übernommen','Zwischenzustand während der Übertragung und Zuordnung.',booking('BITTE WARTEN',YELLOW,hint='Check-in wird aktualisiert',border=False))
add('Verbindung / Daten fehlen','Kein bestätigter Belegungsstatus; keine grüne Freigabe. Auch veraltete Buchungsdaten werden kenntlich gemacht.',booking('STATUS OFFEN',YELLOW,when='Buchungen nicht aktuell',hint='Verbindung zu Home Assistant',border=False))
add('Statusfehler','Fehlerzustand der Arbeitsplatzzuordnung. Details werden in Home Assistant geprüft.',booking('BITTE PRUEFEN',YELLOW,hint='Status in Home Assistant pruefen',border=False))
add('Licht dimmen','Drehen im Bedienmodus oder den Ring berühren. Ein-/Aus-Tasten; untere Leiste wechselt die Funktion, obere Symbolleiste die Lampe.',lighting())
add('Weitere Lichtseite','Bis zu vier zugeordnete Lichter mit eigenen Namen und Symbolen. Beispielnamen, nicht die tatsächliche Gerätezuordnung.',lighting(30,2))
add('Tischhöhe / Favoriten','Höhenregler 62–128 cm und Sitz-/Steh-Favoriten. Beispiele: 74 und 110 cm.',height())
add('Menüauswahl per Drehrad','Grauer Rahmen = Menüauswahl. Drehen wählt die Funktion; Drücken öffnet den Bedienmodus. Erneutes Drücken kehrt zurück.',height(selecting=True))
add('Rollo / Position','Positionssteuerung. Die Seite erscheint nur bei zugeordnetem Rollo; ohne Lamellenfähigkeit fehlt deren Steuerung.',cover(False))
add('Jalousie / Lamellen','Position und Lamellen getrennt. Per Touch Höhe oder Lamellen als Drehradfunktion auswählen.',cover())
add('Schaltkanal','Ein und Aus per Touch. Im Bedienmodus: rechts drehen = ein, links drehen = aus. Name und Symbol konfigurierbar.',switch())
add('Check-in-Bestätigung','Willkommensnachricht mit grünem animiertem Ring; Check-out verwendet dieselbe Meldungsart. Standbild einer Animation.',message('Willkommen, Alex Beispiel',GREEN))
add('Check-in abgewiesen','Belegter oder für eine andere Person reservierter Arbeitsplatz. Roter animierter Ring. Standbild einer Animation.',message('Bereits gebucht...',RED))
add('Reservierung endet bald','Warnung ab 30 Minuten Restzeit bei eingecheckter Person; roter animierter Ring. Langer Text ist scrollbar.',message('Achtung, Reservierung endet bald. Bitte nachbuchen, falls benötigt...',RED))
add('Push · hohe Priorität','Priorität 1: rot animiert. Einzel-, Gruppen- und zentrale Nachrichten nutzen dieselbe Oberfläche.',message('Bitte zum Empfang kommen.',RED))
add('Push · mittlere Priorität','Priorität 2: gelb animiert; Anzeigedauer konfigurierbar. OK schließt die Nachricht.',message('Das Teammeeting beginnt in 10 Minuten.',YELLOW))
add('Push · normale Priorität','Priorität 3: ohne Ring. Nach Ablauf oder Bestätigung kehrt die vorige Ansicht zurück.',message('Das Mittagessen ist angekommen.'))
add('Standby','Beispiel einer gedimmten Ansicht. Wartezeit, Helligkeit und Rückkehr zum Check-in-Dashboard sind konfigurierbar.',ImageEnhance.Brightness(booking()).enhance(.2))
add('Display ausgeschaltet','Display-Aktiv aus: schwarzes Panel. Gewöhnliche Bedienung soll es nicht wieder einschalten.',Image.new('RGB',(480*S,480*S),'black'))
add('Geplant: eingecheckt','Vorgesehene Änderung: GEBUCHT blau, ohne Ring; Mitarbeitername nur einmal, keine Wiederholung oben/unten. Noch nicht aufgespielt.',booking('GEBUCHT','#268dff','Alex Beispiel',when='Reserviert bis 16.11. 12:00',hint='Dein Arbeitsplatz',border=False,planned=True),'Geplant')

# Four compact sheets plus a separate proposed state; standalone PNGs remain readable.
for start in range(0,len(screens),6):
    subset=screens[start:start+6];sheet=Image.new('RGB',(1560,100+590*((len(subset)+2)//3)),'#080c12')
    d=ImageDraw.Draw(sheet);d.text((26,15),'DISPLAY · MENÜS UND ZUSTÄNDE',font=ImageFont.truetype(str(BOLD),28),fill='white')
    d.text((26,56),'Illustrative Nachbildungen aus Firmware · Beispielwerte · keine Live-Aufnahmen',font=ImageFont.truetype(str(FONT),18),fill='#a9bbc9')
    for n,s in enumerate(subset):sheet.paste(Image.open(OUT/s['file']).resize((520,590)),((n%3)*520,100+(n//3)*590))
    sheet.save(OUT/f'uebersicht-{start//6+1}.png')
intro='Diese Bildschirmbeispiele wurden anhand der lokalen Firmware schreibtisch-display-01.reserved.redacted.yaml und der Integrationsdokumentation nachgebildet. Sie sind keine Screenshots des Geräts und keine pixelgenaue LVGL-Emulation. Schrift, Icons, Umbruch und Leuchteffekte können abweichen. Namen, Uhrzeiten, Werte und Gerätezuordnungen sind Beispiele. Animationen sind als Standbild dargestellt. Es wurden keine Geräte bedient, Nachrichten gesendet oder Firmwareänderungen vorgenommen.'
body=''.join(f'<article><h2>{i+1:02d} · {html.escape(s["title"])}</h2><a href="{s["file"]}"><img src="{s["file"]}" alt="{html.escape(s["title"])}"></a><p>{html.escape(s["description"])}</p></article>' for i,s in enumerate(screens))
(OUT/'index.html').write_text('<!doctype html><html lang="de"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Display-Beispiele</title><style>body{background:#080c12;color:#f1f5f9;font:16px/1.6 system-ui;margin:32px auto;max-width:1500px;padding:20px}header{max-width:1000px}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:24px}article{background:#111c27;border-radius:16px;padding:20px}h2{font-size:20px}img{width:100%}p{color:#b5c5d5}a{color:#00d2ff}</style><header><h1>Display: Menüführung und Funktionen</h1><p>'+html.escape(intro)+'</p><p>Navigation: Arbeitsplatz → Licht → Höhe → Rollo/Jalousie → Schaltkanal. Nicht zugeordnete Funktionen werden ausgeblendet. Touch-Symbole oder Wischen wechseln die Seite; der Drehrad-Auswahlmodus ist grau markiert, der Bedienmodus türkis. Diagnosesensoren und globale Konfiguration liegen in Home Assistant, nicht in einem weiteren Display-Menü.</p></header><main>'+body+'</main></html>',encoding='utf-8')
(OUT/'README.md').write_text('# Display-Beispiele\n\n'+intro+'\n\n'+ '\n\n'.join(f'{i+1:02d}. **{s["title"]}** — {s["description"]}' for i,s in enumerate(screens)),encoding='utf-8')
with zipfile.ZipFile(OUT.parent/'display-beispiele.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in OUT.iterdir():
        if p.suffix in ('.png','.html','.md'):z.write(p,p.name)
print(f'{len(screens)} screen examples, 5 sheets, HTML gallery and ZIP created.')
