"""App name to package name mapping for supported applications."""

APP_PACKAGES: dict[str, str] = {
    "微信": "weixin://",
    "WeChat": "weixin://",
    "小红书": "xhsdiscover://home",
    "RedNote": "xhsdiscover://home",
    "淘宝": "taobao://",
    "taobao": "taobao://",
    "微博": "sinaweibo://gotohome",
    "weibo": "sinaweibo://gotohome",
    "支付宝": "alipay://",
    "alipay": "alipay://",
    "相机": "Camera://",
    "Camera": "Camera://",
    "笔记": "Notes://",
    "Notes": "Notes://",
    "qunar": "qunariphone://home?module=main",
    "去哪儿": "qunariphone://home?module=main",
    "京东": "openapp.jdmobile://",
    "JD": "openapp.jdmobile://",
}


def get_package_name(app_name: str) -> str | None:
    """
    Get the package name for an app.

    Args:
        app_name: The display name of the app.

    Returns:
        The Android package name, or None if not found.
    """
    return APP_PACKAGES.get(app_name)


def get_app_name(package_name: str) -> str | None:
    """
    Get the app name from a package name.

    Args:
        package_name: The Android package name.

    Returns:
        The display name of the app, or None if not found.
    """
    for name, package in APP_PACKAGES.items():
        if package == package_name:
            return name
    return None


def list_supported_apps() -> list[str]:
    """
    Get a list of all supported app names.

    Returns:
        List of app names.
    """
    return list(APP_PACKAGES.keys())
