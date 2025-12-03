from django.db import models


# 1. Tu catálogo
class Producto(models.Model):
    codigo = models.CharField(max_length=10, unique=True)
    nombre = models.CharField(max_length=100)
    precio = models.DecimalField(max_digits=6, decimal_places=2)
    
    def __str__(self):
        return f"{self.nombre} (${self.precio})"

# 2. Los pedidos existentes
class Pedido(models.Model):
    numero_pedido = models.CharField(max_length=20, unique=True)
    estado = models.CharField(max_length=50) # Ej: "En camino", "Entregado"
    
    def __str__(self):
        return f"Pedido {self.numero_pedido}: {self.estado}"

# 3. La memoria del bot (Máquina de Estados)
class SesionUsuario(models.Model):
    telefono = models.CharField(max_length=20, unique=True)
    # Estados posibles: 'MENU', 'ESPERANDO_CODIGO_PRODUCTO', 'CONFIRMANDO_COMPRA', 'ESPERANDO_NUMERO_PEDIDO'
    estado_actual = models.CharField(max_length=50, default='MENU')
    # Guardamos temporalmente el producto que le interesó para cuando diga "Sí"
    producto_interes_id = models.IntegerField(null=True, blank=True)


class LogMensaje(models.Model):
    # Campos de nuestra tabla
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    telefono = models.CharField(max_length=20)
    mensaje = models.TextField()
    
    def __str__(self):
        return f"{self.telefono}: {self.mensaje}"