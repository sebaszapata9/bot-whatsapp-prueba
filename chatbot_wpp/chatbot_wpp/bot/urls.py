from django.urls import path
from . import views

#path nos permite tener multiples urls dentro de una lista

urlpatterns = [
	path('webhook/',views.webhook, name="webhook")
	]

# views hace referencia al renderizado html
# index hace referencia a la función creada en archivo views.py
	
"""

que la ruta tenga nomenclatura '' significa que es la ruta principal
ejm: mercadolibre.com.pe

Si en vez de '' fuera /productos, entonces la dirección a la que haría
referencia sería mercadolibre.com.pe/productos

"""