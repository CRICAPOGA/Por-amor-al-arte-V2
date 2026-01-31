from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.utils.text import slugify

# -----------------------
# Usuario personalizado
# -----------------------
class CustomUser(AbstractUser):
    """
    Usuario base. Usa el campo email para autenticación con Google si lo deseas.
    Puedes añadir más flags si necesitas (ej: is_staff_artist, etc.)
    """
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.username

# -----------------------
# Linea Artistica y Generos
# -----------------------
class LineaArtistica(models.Model):
    """
    Línea artística (p. ej. 'Música', 'Danza', 'Teatro', etc.)
    """
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nombre

class Genero(models.Model):
    """
    Género (pertenece a una línea artística)
    """
    nombre = models.CharField(max_length=100)
    linea = models.ForeignKey(LineaArtistica, on_delete=models.PROTECT, related_name='generos')

    class Meta:
        unique_together = ('nombre', 'linea')

    def __str__(self):
        return f"{self.nombre} ({self.linea.nombre})"

# -----------------------
# Perfiles de Artista
# -----------------------
class ArtistProfile(models.Model):
    """
    Perfil asociado a un usuario que es artista independiente.
    Muchos usuarios pueden no tener ArtistProfile; crearlo cuando el usuario
    se registre como artista.
    """
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='artist_profile')
    nombre_artistico = models.CharField(max_length=150, blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    perfil_imagen = models.ImageField(upload_to='artists/profile/', blank=True, null=True)
    # géneros (max 3) -> validación en clean()
    generos = models.ManyToManyField(Genero, blank=True, related_name='artistas')
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    def clean(self):
        # validar max 3 generos
        if self.pk:
            generos_count = self.generos.count()
        else:
            # si no está guardado aún, no podemos contar m2m; será validado en el formulario o después
            generos_count = 0
        if generos_count > 3:
            raise ValidationError("Un artista puede seleccionar como máximo 3 géneros.")

    def __str__(self):
        return self.nombre_artistico or f"{self.user.get_full_name() or self.user.username}"

# -----------------------
# Agrupación
# -----------------------
class Agrupacion(models.Model):
    """
    Agrupación musical/artistica. Admin es un usuario (el que creó/gestiona la agrupación).
    Los miembros serán ArtistProfile (artistas).
    """
    nombre = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    administrador = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='agrupaciones_administradas')
    descripcion = models.TextField(blank=True, null=True)
    perfil_imagen = models.ImageField(upload_to='groups/profile/', blank=True, null=True)
    miembros = models.ManyToManyField(ArtistProfile, blank=True, related_name='agrupaciones')
    # géneros (max 3) -> validación en clean()
    generos = models.ManyToManyField(Genero, blank=True, related_name='agrupaciones')
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.nombre)[:180]
            slug = base
            counter = 1
            while Agrupacion.objects.filter(slug=slug).exists():
                slug = f"{base}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def clean(self):
        # Validar max 3 generos (si ya existen m2m -> contar)
        if self.pk:
            if self.generos.count() > 3:
                raise ValidationError("Una agrupación puede seleccionar como máximo 3 géneros.")

    def __str__(self):
        return self.nombre

# -----------------------
# Imágenes (Artista y Agrupación)
# -----------------------
class ArtistImage(models.Model):
    artist = models.ForeignKey(ArtistProfile, on_delete=models.CASCADE, related_name='imagenes')
    imagen = models.ImageField(upload_to='artists/images/')
    titulo = models.CharField(max_length=150, blank=True, null=True)
    orden = models.PositiveSmallIntegerField(default=0)
    creado_en = models.DateTimeField(auto_now_add=True)

    def clean(self):
        # Limitar a 5 imágenes por artista
        if self.pk:
            existing = ArtistImage.objects.filter(artist=self.artist).exclude(pk=self.pk).count()
        else:
            existing = ArtistImage.objects.filter(artist=self.artist).count()
        if existing >= 5:
            raise ValidationError("Un artista puede subir máximo 5 imágenes.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Imagen {self.id} - {self.artist}"

class GroupImage(models.Model):
    agrupacion = models.ForeignKey(Agrupacion, on_delete=models.CASCADE, related_name='imagenes')
    imagen = models.ImageField(upload_to='groups/images/')
    titulo = models.CharField(max_length=150, blank=True, null=True)
    orden = models.PositiveSmallIntegerField(default=0)
    creado_en = models.DateTimeField(auto_now_add=True)

    def clean(self):
        # Limitar a 5 imágenes por agrupación
        if self.pk:
            existing = GroupImage.objects.filter(agrupacion=self.agrupacion).exclude(pk=self.pk).count()
        else:
            existing = GroupImage.objects.filter(agrupacion=self.agrupacion).count()
        if existing >= 5:
            raise ValidationError("Una agrupación puede subir máximo 5 imágenes.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Imagen {self.id} - {self.agrupacion.nombre}"

# -----------------------
# Redes sociales (Artista y Agrupación)
# -----------------------
class SocialPlatformChoices(models.TextChoices):
    FACEBOOK = 'facebook', 'Facebook'
    INSTAGRAM = 'instagram', 'Instagram'
    TWITTER = 'twitter', 'Twitter'
    YOUTUBE = 'youtube', 'YouTube'
    TIKTOK = 'tiktok', 'TikTok'
    SPOTIFY = 'spotify', 'Spotify'
    OTHER = 'other', 'Other'

class ArtistSocial(models.Model):
    artist = models.ForeignKey(ArtistProfile, on_delete=models.CASCADE, related_name='redes')
    plataforma = models.CharField(max_length=30, choices=SocialPlatformChoices.choices, default=SocialPlatformChoices.OTHER)
    url = models.URLField()
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.artist} - {self.plataforma}"

class GroupSocial(models.Model):
    agrupacion = models.ForeignKey(Agrupacion, on_delete=models.CASCADE, related_name='redes')
    plataforma = models.CharField(max_length=30, choices=SocialPlatformChoices.choices, default=SocialPlatformChoices.OTHER)
    url = models.URLField()
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.agrupacion.nombre} - {self.plataforma}"
