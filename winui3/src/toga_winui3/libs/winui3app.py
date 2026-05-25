########################################################################################
# WinUI3App is derived from Yukihiro Nakadaira's XamlApplication:
# github.com/ynkdir/py-win32more/blob/main/packages/appsdk/src/win32more/winui3/__init__.py  # noqa: E501
#
# ======================================================================================
#
# MIT License
#
# Copyright (c) 2022 Yukihiro Nakadaira
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# ======================================================================================
#
########################################################################################

from __future__ import annotations

import inspect
from pathlib import Path

from win32more import FAILED, Char, ComClass, WinError
from win32more.Microsoft.UI.Xaml import Application, IApplicationOverrides, Window
from win32more.Microsoft.UI.Xaml.Markup import IXamlMetadataProvider
from win32more.Microsoft.UI.Xaml.XamlTypeInfo import XamlControlsXamlMetaDataProvider
from win32more.Microsoft.Windows.ApplicationModel.Resources import (
    ResourceCandidate,
    ResourceCandidateKind,
    ResourceManager,
)
from win32more.Windows.Foundation import Uri
from win32more.Windows.Win32.System.Com import (
    COINIT_APARTMENTTHREADED,
    CoInitializeEx,
    CoUninitialize,
)
from win32more.Windows.Win32.System.LibraryLoader import GetModuleFileName

# TODO: Clean up code.
# TODO: Needs to be commented and explained.
# FIXME: Fix resources.


class WinUI3App(ComClass, Application, IApplicationOverrides, IXamlMetadataProvider):
    def __init__(self):
        WinUI3App.__current = self
        self._provider = None
        super().__init__(own=True)
        self.InitializeComponent()
        self.ResourceManagerRequested += self.OnResourceManagerRequested

    def InitializeComponent(self):
        xaml_path = Path(__file__).parent.parent / "resources" / "winui3app.xaml"
        resource_locator = Uri(f"ms-appx:///{xaml_path.as_posix()}")
        Application.LoadComponent(self, resource_locator)

    def OnLaunched(self, args): ...

    def OnExited(self): ...

    # FIXME: Find a way to remove this method.
    def CreateWindow(self):
        return Window()

    def GetXamlType(self, type):
        return self.AppProvider().GetXamlType(type)

    # TODO: Is it needed to provide information for primitive or winui type?
    def GetXamlTypeByFullName(self, fullName):
        return self.AppProvider().GetXamlTypeByFullName(fullName)

    def GetXmlnsDefinitions(self):
        return self.AppProvider().GetXmlnsDefinitions()

    def AppProvider(self):
        if self._provider is None:
            self._provider = XamlControlsXamlMetaDataProvider()
        return self._provider

    # FIXME: When executing app execution alias, sys.executable points alias.
    #   sys.executable => $LOCALAPPDATA\Microsoft\WindowsApps\python.exe
    # We need resolved path instead.
    def AppExecutable(self) -> Path:
        buf = (Char * 1024)()
        r = GetModuleFileName(None, buf, 1024)
        if r == 0:
            raise WinError()
        return Path(buf.value)

    # Application root path.  This is used to convert "ms-appx:///" path.  See
    # OnResourceNotFound(). This does not affect to WindowsAppSDK and may not work
    # in specific situation. Appsdk's default is directory of python.exe file.
    def AppRoot(self) -> Path:
        # return self.AppExecutable().parent
        return Path(inspect.getfile(type(self))).parent

    def OnResourceManagerRequested(self, sender, e):
        # Workaround to avoid FileNotFoundError with default constructor (file does
        # not need to exist). https://github.com/microsoft/WindowsAppSDK/issues/5814
        manager = ResourceManager("resources.pri")
        manager.ResourceNotFound += self.OnResourceNotFound
        e.CustomResourceManager = manager

    def OnResourceNotFound(self, sender, e):
        name = e.Name
        print(f"OnResourceNotFound: {name}")
        if name.startswith("Files/file:///") and name.endswith(".png"):
            resource_candidate = ResourceCandidate(
                ResourceCandidateKind.FilePath, str(name)
            )
            e.SetResolvedCandidate(resource_candidate)
            # ignore absolute path
            pass
        elif e.Name.startswith("Files/"):
            # convert relative path from ms-appx:///path/to/file to
            # AppRoot()/path/to/file
            name = name.removeprefix("Files/")
            filepath = self.__tmp_resource_file.pop(name, self.AppRoot() / name)
            if filepath.exists():
                resource_candidate = ResourceCandidate(
                    ResourceCandidateKind.FilePath, str(filepath)
                )
                e.SetResolvedCandidate(resource_candidate)

    __tmp_resource_file = {}

    __current = None

    @classmethod
    def Start(cls):

        hr = CoInitializeEx(None, COINIT_APARTMENTTHREADED)
        if FAILED(hr):
            raise WinError(hr)

        def ApplicationInitializationCallback(*_args):
            return cls()

        Application.Start(ApplicationInitializationCallback)

        # FIXME: force Release() to avoid exit with error code.
        if WinUI3App.__current is not None:
            WinUI3App.__current.OnExited()
            WinUI3App.__current.Release()

        CoUninitialize()
