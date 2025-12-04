from django.contrib import admin
from .models import Producto, Pedido, SesionUsuario, LogMensaje

admin.site.register(Producto)
admin.site.register(Pedido)
admin.site.register(SesionUsuario)
admin.site.register(LogMensaje)