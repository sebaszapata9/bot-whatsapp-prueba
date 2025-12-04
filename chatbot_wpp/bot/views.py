from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Producto, Pedido, SesionUsuario, LogMensaje
import json
import requests
import os

# Ya no escribimos el token aquí. Le decimos al código:
# "Busca una variable llamada META_ACCESS_TOKEN en el servidor"
ACCESS_TOKEN = os.environ.get('META_ACCESS_TOKEN') 
PHONE_NUMBER_ID = os.environ.get('META_PHONE_ID')
# ---------------------------------------------------------

@csrf_exempt
def webhook(request):
    # 1. VERIFICACIÓN (GET)
    if request.method == 'GET':
        token_verificacion = "HOLA_MUNDO_TOKEN"
        if request.GET.get('hub.verify_token') == token_verificacion:
            return HttpResponse(request.GET.get('hub.challenge'))
        return HttpResponse("Error", status=403)

    # 2. RECEPCIÓN (POST)
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            entry = data.get('entry', [])[0]
            changes = entry.get('changes', [])[0]
            value = changes.get('value', {})
            messages = value.get('messages', [])

            if messages:
                mensaje_obj = messages[0]
                
                # Verificamos que sea texto
                if mensaje_obj.get('type') == 'text':
                    numero = mensaje_obj['from']
                    texto = mensaje_obj['text']['body']
                    
                    print(f"📩 CLIENTE ({numero}): {texto}")
                    
                    # Log en BD
                    LogMensaje.objects.create(telefono=numero, mensaje=texto)
                    
                    # --- CEREBRO DEL NEGOCIO ---
                    respuesta = manejar_flujo_negocio(numero, texto)
                    
                    # --- ENVÍO DE RESPUESTA ---
                    enviar_mensaje_whatsapp(numero, respuesta)
                else:
                    print("⚠️ Recibí imagen/audio/etc. Ignorado por ahora.")

            return HttpResponse("EVENT_RECEIVED", status=200)

        except Exception as e:
            print(f"❌ ERROR: {e}")
            return HttpResponse("Error", status=500)
    
    return HttpResponse("OK", status=200)


def manejar_flujo_negocio(telefono, texto):
    texto = texto.strip().lower()
    
    # Recuperamos la memoria del usuario (Estado actual)
    sesion, created = SesionUsuario.objects.get_or_create(telefono=telefono)
    
    # RESETEO DE EMERGENCIA
    if texto in ['hola', 'menu', 'inicio', 'salir']:
        sesion.estado_actual = 'MENU'
        sesion.producto_interes_id = None
        sesion.save()
        return (
            "💪 *IronSnacks - Nutrición Inteligente*\n"
            "Bienvenido. Selecciona una opción:\n\n"
            "1️⃣ Ver Catálogo y Comprar\n"
            "2️⃣ Consultar estado de mi pedido\n"
            "3️⃣ Hablar con un asesor humano"
        )

    # --- MÁQUINA DE ESTADOS ---
    
    # 1. EN EL MENÚ
    if sesion.estado_actual == 'MENU':
        if texto == '1':
            sesion.estado_actual = 'ESPERANDO_CODIGO_PRODUCTO'
            sesion.save()
            return (
                "📄 Aquí tienes nuestro catálogo: https://tinyurl.com/catalogo-iron\n\n"
                "Por favor, escribe el *CÓDIGO* del producto que deseas (Ej: P01)."
            )
        elif texto == '2':
            sesion.estado_actual = 'ESPERANDO_NUMERO_PEDIDO'
            sesion.save()
            return "📦 Por favor, ingresa tu número de pedido para rastrearlo."
        elif texto == '3':
            return "👨‍💻 Un asesor ha sido notificado. Te escribirá en breve."
        else:
            return "Opción no válida. Escribe 1, 2 o 3."

    # 2. ESPERANDO CÓDIGO (Ej: P01)
    elif sesion.estado_actual == 'ESPERANDO_CODIGO_PRODUCTO':
        try:
            producto = Producto.objects.get(codigo__iexact=texto)
            sesion.producto_interes_id = producto.id
            sesion.estado_actual = 'CONFIRMANDO_COMPRA'
            sesion.save()
            return (
                f"Has seleccionado: *{producto.nombre}* a S/{producto.precio}\n"
                "¿Deseas confirmar la compra? Responde *SI* o *NO*."
            )
        except Producto.DoesNotExist:
            return "❌ Código no encontrado. Intenta nuevamente (Ej: P01) o escribe 'menu' para salir."

    # 3. CONFIRMANDO COMPRA (SI/NO)
    elif sesion.estado_actual == 'CONFIRMANDO_COMPRA':
        if texto == 'si':
            try:
                producto = Producto.objects.get(id=sesion.producto_interes_id)
                monto = producto.precio
            except:
                monto = "0.00"
            
            sesion.estado_actual = 'MENU' # Fin del flujo
            sesion.save()
            return (
                f"¡Excelente! 🚀\nTotal a pagar: S/{monto}\n\n"
                f"📲 Yape al: *999-999-999*\n"
                "Envíanos la constancia por aquí. ¡Gracias!"
            )
        elif texto == 'no':
            sesion.estado_actual = 'MENU'
            sesion.save()
            return "Operación cancelada. Escribe 'Hola' para volver al menú."
        else:
            return "Por favor responde SI o NO."

    # 4. RASTREANDO PEDIDO
    elif sesion.estado_actual == 'ESPERANDO_NUMERO_PEDIDO':
        try:
            pedido = Pedido.objects.get(numero_pedido__iexact=texto)
            sesion.estado_actual = 'MENU'
            sesion.save()
            return f"✅ El estado de tu pedido {texto} es: *{pedido.estado}*"
        except Pedido.DoesNotExist:
            return "❌ No encontramos ese pedido. Intenta de nuevo."

    return "No entendí. Escribe 'Hola' para ver el menú."


def enviar_mensaje_whatsapp(telefono, mensaje):
    url = f"https://graph.facebook.com/v17.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": telefono,
        "type": "text",
        "text": {"body": mensaje}
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            print("✅ RESPUESTA ENVIADA.")
        else:
            print(f"⚠️ ERROR META: {response.text}")
    except Exception as e:
        print(f"❌ ERROR CONEXIÓN: {e}")