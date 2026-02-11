import cloudinary.utils
from cloudinary_storage.storage import MediaCloudinaryStorage


class OptimizedMediaCloudinaryStorage(MediaCloudinaryStorage):
    """
    Extends MediaCloudinaryStorage to automatically apply
    Cloudinary's f_auto (format) and q_auto (quality) optimizations
    to all generated image URLs.
    """

    def _get_url(self, name):
        name = self._prepend_prefix(name)
        resource_type = self._get_resource_type(name)
        url, _ = cloudinary.utils.cloudinary_url(
            name,
            resource_type=resource_type,
            quality='auto',
            fetch_format='auto',
        )
        return url
