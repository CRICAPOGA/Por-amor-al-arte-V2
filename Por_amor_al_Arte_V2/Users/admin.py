from django.contrib import admin
from .models import CustomUser, LineaArtistica, Genero, ArtistProfile, Agrupacion, ArtistImage, GroupImage, SocialPlatformChoices, ArtistSocial, GroupSocial

# Register your models here.
admin.site.register(CustomUser)
admin.site.register(LineaArtistica)
admin.site.register(Genero)
admin.site.register(ArtistProfile)
admin.site.register(Agrupacion)
admin.site.register(ArtistImage)
admin.site.register(GroupImage)
admin.site.register(ArtistSocial)
admin.site.register(GroupSocial)