# Flet Compatibility Issue with Fedora 43

## Issue Description
When running Flet applications on Fedora 43, the application windows appear blank due to compatibility issues with the underlying GTK/OpenGL components. The application runs but shows errors related to:

- ATk accessibility components
- GTK window positioning and sizing
- OpenGL context issues
- Flutter engine view management

## Error Messages
```
Atk-CRITICAL **: atk_socket_embed: assertion 'plug_id != NULL' failed
Gtk-CRITICAL **: gtk_window_get_position: assertion 'GTK_IS_WINDOW (window)' failed
Gtk-CRITICAL **: gtk_window_get_size: assertion 'GTK_IS_WINDOW (window)' failed
WARNING **: Failed to cleanup compositor shaders, unable to make OpenGL context current
embedder.cc (2575): 'FlutterEngineRemoveView' returned 'kInvalidArguments'
```

## Solutions

### 1. Updated Flet Version
We've updated to the latest Flet version (0.80.1) which has some improvements for Linux compatibility.

### 2. Environment Variables Workaround
Try running the application with these environment variables:

```bash
GDK_BACKEND=x11 LIBGL_ALWAYS_SOFTWARE=1 WEBKIT_DISABLE_COMPOSITING_MODE=1 python main.py
```

### 3. Alternative: Use Web Mode
Flet can run in web mode which avoids the desktop rendering issues:

```bash
flet run main.py --web
```

### 4. Alternative: Use Container
Consider running the application in a container with a stable environment:

```bash
podman run -it --rm -v $(pwd):/app -w /app python:3.11 bash
pip install -r requirements.txt
python main.py
```

## Additional Notes

1. Fedora 43 uses newer versions of GTK and graphics libraries that may conflict with Flet's Flutter-based rendering engine
2. The issue is related to the underlying Flutter engine's interaction with Linux graphics systems
3. This is a known issue with Flet on newer Linux distributions
4. Consider using the web version of your application as a temporary workaround

## Running with Workarounds

A script `run_flet_app.py` has been created to run the application with Fedora 43 compatibility workarounds. You can run it using:

```bash
python run_flet_app.py
```

Or directly with environment variables:

```bash
GDK_BACKEND=x11 LIBGL_ALWAYS_SOFTWARE=1 WEBKIT_DISABLE_COMPOSITING_MODE=1 GDK_DISABLE_ABSTRACT_SOCKETS=1 python main.py