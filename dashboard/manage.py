#!/usr/bin/env python
"""Entry point Django - dijalankan dari dalam folder dashboard/.

    cd dashboard
    python manage.py migrate
    python manage.py createsuperuser
    python manage.py runserver 0.0.0.0:8001
"""

import os
import sys


def main() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Django tidak ketemu - jalankan `pip install -r ../requirements.txt` dulu"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
