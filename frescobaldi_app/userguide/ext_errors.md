=== Handling Errors in Extensions ===

As extensions are third-party software Frescobaldi has no control over how
reliable they work. However, great care has been taken to minimize the potential
problems caused by faulty extensions.

*NOTE:* It has already been said but it can't be overstated: extension code gets
access to Frescobaldi's complete code base which makes them very powerful. But
at the same time extensions have access to the full power of the Python
programming language, so the privileges of the user account Frescobaldi is
running under are the only restrictions to what extension code is allowed to do
on your computer. Please make sure that you only run extensions from sources
you trust, Frescobaldi has no way to preventing faulty or malign code from
being executed.

== Problems While Loading Extensions ==

There are several reasons why extensions may cause problems while loading. These
are reported by a pop-up dialog while loading Frescobaldi.

* *Errors in the metadata file.* Each extension has a metadata file. If there
  are entries missing or other parsing errors the extension is loaded anyway,
  with some fallback values in place. However, this *may* cause arbitrary
  problems, and you are encouraged to report such issues to the extension's
  maintainer.
* *Failed dependencies.* Extensions may depend on other extensions. Frescobaldi
  will ensure the extensions are loaded in the appropriate order to prevent
  errors while loading an extension. It is considered an error if an extension
  declares a dependency and the corresponding extension is not installed.
  Another type of error are circular dependencies. Both types are shown in the
  pop-up dialog, and the affected extensions are *not* loaded.
* *Errors while loading.* If an error occurs while loading the extension code
  the extension is deactivated automatically. The entry in the pop-up dialog
  will show a one-line explanation of the error, and double-clicking on that
  entry will open a pop-up with the full Python exception. When reporting the
  problem to the extension maintainer this information should be included.

The content of this message box will also be accessible at a later point through
{menu_preferences_extensions_failed}.

== Problems at Runtime ==

Errors in extensions may not become apparent during program start but only
later, which is reported differently.

If an error occurs while creating an extension's Tool Panel The panel will be
replaced by a dummy panel indicating the problem.

If an extension produces a runtime error it is reported by a pop-up dialog. This
is nearly the same as the dialog for general error reports but it tries to
determine which extension has caused the error. The dialog tries to extract the
extension maintainer information and (if successful) lets you send the error
report directly to the registered maintainer's email address.

#VARS

menu_preferences_extensions    menu Edit -> Preferences -> Extensions
menu_preferences_extensions_failed    menu Edit -> Preferences -> Extensions -> Failed Extensions
