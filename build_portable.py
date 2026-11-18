import os
import shutil
import subprocess
import sys


PROJECT = os.path.abspath(
    os.path.dirname(__file__)
)

DIST = os.path.join(
    PROJECT,
    "dist",
    "desktop_django"
)


def copy_item(name):

    source = os.path.join(
        PROJECT,
        name
    )

    destination = os.path.join(
        DIST,
        name
    )

    if not os.path.exists(source):

        print(
            f"[WARNING] غير موجود: {source}"
        )

        return

    if os.path.isdir(source):

        if os.path.exists(destination):
            shutil.rmtree(destination)

        shutil.copytree(
            source,
            destination
        )

    else:

        shutil.copy2(
            source,
            destination
        )

    print(
        f"[OK] تم نسخ: {name}"
    )


def main():

    print("=" * 60)
    print("BUILD PORTABLE DJANGO")
    print("=" * 60)

    # --------------------------------------------------------
    # بناء EXE
    # --------------------------------------------------------

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--clean",
            "--onedir",
            "--console",
            "--name",
            "desktop_django",
            "desktop_django.py",
        ],
        cwd=PROJECT
    )

    if result.returncode != 0:

        print(
            "[ERROR] فشل PyInstaller"
        )

        sys.exit(
            result.returncode
        )

    # --------------------------------------------------------
    # التأكد من مجلد dist
    # --------------------------------------------------------

    if not os.path.isdir(DIST):

        print(
            "[ERROR] لم يتم إنشاء:"
        )

        print(
            DIST
        )

        sys.exit(1)

    # --------------------------------------------------------
    # ملفات Django
    # --------------------------------------------------------

    copy_item("manage.py")
    copy_item("db.sqlite3")
    copy_item("erea")
    copy_item("masha")

    # --------------------------------------------------------
    # مجلدات اختيارية
    # --------------------------------------------------------

    copy_item("templates")
    copy_item("static")
    copy_item("media")

    print()
    print("=" * 60)
    print("تم إنشاء النسخة المحمولة")
    print("=" * 60)
    print()
    print(DIST)
    print()

    print(
        "المحتويات:"
    )

    for item in os.listdir(DIST):

        print(
            "  ",
            item
        )


if __name__ == "__main__":
    main()