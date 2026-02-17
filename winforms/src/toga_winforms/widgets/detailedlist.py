from ctypes import POINTER, byref, c_wchar_p, cast, sizeof
from ctypes.wintypes import HWND, LPARAM, RECT, SIZE, UINT, WPARAM
from math import floor

import System.Windows.Forms as WinForms
from System.Drawing import Size

from toga.handlers import WeakrefCallable
from toga.sources import Row
from toga.sources.columns import AccessorColumn

from ..libs import windowconstants as wc
from ..libs.comctl32 import (
    DefSubclassProc,
    InitCommonControlsEx,
    RemoveWindowSubclass,
    SetWindowSubclass,
)
from ..libs.comctl32classes import INITCOMMONCONTROLSEX, LVCOLUMNW, LVTILEVIEWINFO
from ..libs.user32 import (
    CreateWindowExW,
    GetSystemMetrics,
    GetWindowLongPtrW,
    GetWindowRect,
    SendMessageW,
    SetWindowPos,
)
from ..libs.user32classes import NMHDR, NMLVDISPINFOW, SUBCLASSPROC
from ..libs.win32 import HIWORD, LONG_PTR, LOWORD, LRESULT, is_submessage, str_pixels
from .box import Box

# Columns to adapt DetailedList source to Table.
COLUMNS = (AccessorColumn(None, "title"), AccessorColumn(None, "subtitle"))


# Wrap a DetailedList source to make it compatible with a Table.
class TableSource:
    def __init__(self, interface):
        self.interface = interface

    def __len__(self):
        return len(self.interface.data)

    def __getitem__(self, index):
        row = self.interface.data[index]
        title, subtitle, icon = (
            getattr(row, attr, None) for attr in self.interface.accessors
        )
        return Row(title=(icon, title), subtitle=subtitle)


class DetailedList(Box):
    @property
    def _columns(self):
        return COLUMNS

    @property
    def _data(self):
        return self._table_source

    def __del__(self):
        # The object self.pfn_subclass is a python class and is part of the native
        # Windows process. When a DetailedList is removed by the python GC,
        # self.pfn_subclass is also removed and the Windows process has a dangling
        # pointer. Calling Dispose() here fixes the problem by removing the
        # self.pfn_subclass from the Windows process.
        self.native.Dispose()

    def create(self):
        super().create()
        self._box_hwnd = int(self.native.Handle.ToString())
        self._table_source = TableSource(self.interface)
        self._cache: dict[int, tuple] = {}
        self._first_item = 0

        # System icon dimensions
        icon_x = GetSystemMetrics(wc.SM_CXICON)
        icon_y = GetSystemMetrics(wc.SM_CYICON)

        # According to the MicroSoft documentation, an application must call
        # InitCommonControlsEx must before creating a common control.
        self._init_common_controls_ex = INITCOMMONCONTROLSEX()
        self._init_common_controls_ex.dwSize = sizeof(INITCOMMONCONTROLSEX)
        self._init_common_controls_ex.dwICC = wc.ICC_LISTVIEW_CLASSES
        InitCommonControlsEx(byref(self._init_common_controls_ex))

        # Create the ListView object.
        # learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-createwindowexw
        initial_style = wc.LVS_OWNERDATA | wc.LVS_SINGLESEL | wc.LVS_REPORT

        self._hwnd = CreateWindowExW(
            wc.LVS_EX_DOUBLEBUFFER,
            wc.WC_LISTVIEW,
            None,
            wc.WS_CHILD | wc.WS_VISIBLE | initial_style,
            0,
            0,
            self._box_dimensions[0],
            self._box_dimensions[1],
            HWND(self._box_hwnd),
            None,
            None,
            None,
        )

        # Define tile-size constants
        self._tile_height = floor(icon_y * 1.5)
        tile_padding = floor(icon_x * 0.25)

        # Change the view style to tile and configure the properties.
        # learn.microsoft.com/en-us/windows/win32/controls/use-tile-views
        SendMessageW(self._hwnd, wc.LVM_SETVIEW, wc.LV_VIEW_TILE, 0)
        lvitemviewinfo = LVTILEVIEWINFO()
        lvitemviewinfo.cbSize = sizeof(lvitemviewinfo)
        lvitemviewinfo.dwMask = (
            wc.LVTVIM_COLUMNS | wc.LVTVIM_TILESIZE | wc.LVTVIM_LABELMARGIN
        )
        lvitemviewinfo.dwFlags = wc.LVTVIF_FIXEDSIZE
        lvitemviewinfo.sizeTile = SIZE(self._tile_width, self._tile_height)
        lvitemviewinfo.cLines = 1
        lvitemviewinfo.rcLabelMargin = RECT(tile_padding, 0, tile_padding, 0)
        SendMessageW(self._hwnd, wc.LVM_SETTILEVIEWINFO, 0, byref(lvitemviewinfo))

        # Create the image list
        self._image_list = WinForms.ImageList()
        self._image_list.ImageSize = Size(icon_x, icon_y)
        image_list_hwnd = int(self._image_list.Handle.ToString())

        # Register the image list
        SendMessageW(
            self._hwnd, wc.LVM_SETIMAGELIST, wc.LVSIL_NORMAL, LPARAM(image_list_hwnd)
        )

        # Create and insert the "subtitles column"
        lvcolumn = LVCOLUMNW()
        lvcolumn.mask = wc.LVCF_SUBITEM
        lvcolumn.iSubItem = 1
        SendMessageW(self._hwnd, wc.LVM_INSERTCOLUMNW, 1, byref(lvcolumn))

        # Create and set the subclass procedure
        self.pfn_subclass = SUBCLASSPROC(self._subclass_proc)
        self._set_subclass()

        # Update the subclass procedure when the native handle is create/destroyed
        self.native.HandleCreated += WeakrefCallable(self.handle_created)
        self.native.HandleDestroyed += WeakrefCallable(self.handle_destroyed)

    def handle_created(self, sender, e):
        # Set the subclass when a handle is created.
        self._box_hwnd = int(self.native.Handle.ToString())
        self._set_subclass()

    def handle_destroyed(self, sender, e):
        # Remove the subclass when a handle is destroyed to prevent a memory leak.
        self._remove_subclass()

    def _set_subclass(self):
        SetWindowSubclass(self._box_hwnd, self.pfn_subclass, 0, 0)

    def _remove_subclass(self):
        RemoveWindowSubclass(self._box_hwnd, self.pfn_subclass, 0)

    def _subclass_proc(
        self,
        hWnd: int,
        uMsg: int,
        wParam: int,
        lParam: int,
        uIdSubclass: int,
        dwRefData: int,
    ) -> LRESULT:
        # Remove the window subclass in the way recommended by Raymond Chen here:
        # devblogs.microsoft.com/oldnewthing/20031111-00/?p=41883
        if uMsg == wc.WM_NCDESTROY:
            RemoveWindowSubclass(hWnd, self.pfn_subclass, uIdSubclass)

        # Handle message to set the ListView item data.
        elif uMsg == wc.WM_NOTIFY:
            phdr = cast(lParam, POINTER(NMHDR)).contents
            code = phdr.code
            if hex(code) == hex(wc.LVN_GETDISPINFOW):
                disp_info = cast(lParam, POINTER(NMLVDISPINFOW)).contents
                self._set_subitem(disp_info.item)

        # Resize ListView to be the same size as the Box container.
        # learn.microsoft.com/en-us/windows/win32/winmsg/wm-size
        elif uMsg == wc.WM_SIZE:
            self._set_list_view_size(LOWORD(lParam), HIWORD(lParam))

        # Call the original window procedure
        return DefSubclassProc(HWND(hWnd), UINT(uMsg), WPARAM(wParam), LPARAM(lParam))

    def _set_subitem(self, lvitem):
        # Set the subitem data in the ListView object.
        # learn.microsoft.com/en-us/windows/win32/api/commctrl/ns-commctrl-lvitemw
        titles, icon_index = self._retrieve_virtual_item(lvitem.iItem)

        if is_submessage(lvitem.uiMask, wc.LVIF_COLUMNS):
            lvitem.cColumns = 1
            puColumns = cast(lvitem.puColumns, POINTER(UINT * 1)).contents
            puColumns[0] = UINT(1)

        if is_submessage(lvitem.uiMask, wc.LVIF_TEXT):
            if lvitem.iSubItem in {0, 1}:
                lvitem.pszText = titles[lvitem.iSubItem]

        if is_submessage(lvitem.uiMask, wc.LVIF_IMAGE):
            lvitem.iImage = icon_index

    def _set_list_view_size(self, width: int, height: int):
        lvitemviewinfo = LVTILEVIEWINFO()
        lvitemviewinfo.cbSize = sizeof(lvitemviewinfo)
        lvitemviewinfo.dwMask = wc.LVTVIM_TILESIZE
        lvitemviewinfo.dwFlags = wc.LVTVIF_FIXEDSIZE
        lvitemviewinfo.sizeTile = SIZE(self._tile_width, self._tile_height)
        SendMessageW(self._hwnd, wc.LVM_SETTILEVIEWINFO, 0, byref(lvitemviewinfo))

        # Tile view has a bug where tile sizes can get "stuck". Manually creating
        # display strings of the correct length and refreshing the list fixes the
        # problem.
        self._cache = {}
        SendMessageW(self._hwnd, wc.LVM_REDRAWITEMS, 0, len(self._data) - 1)

        SetWindowPos(
            self._hwnd,
            self._box_hwnd,
            0,
            0,
            width,
            height,
            wc.SWP_NOMOVE | wc.SWP_NOZORDER | wc.SWP_SHOWWINDOW,
        )

    @property
    def _box_dimensions(self):
        box_rect = RECT()
        GetWindowRect(self._box_hwnd, byref(box_rect))
        return (box_rect.right - box_rect.left, box_rect.bottom - box_rect.top)

    @property
    def _tile_width(self):
        style = LONG_PTR(GetWindowLongPtrW(self._hwnd, wc.GWL_STYLE)).value
        if is_submessage(style, wc.WS_VSCROLL):
            return self._box_dimensions[0] - GetSystemMetrics(wc.SM_CXVSCROLL)

        return self._box_dimensions[0]

    @property
    def _tile_text_width(self):
        return self._tile_width - floor(1.7 * GetSystemMetrics(wc.SM_CXICON))

    def _image_index(self, icon):
        images = self._image_list.Images
        key = str(icon.path)
        index = images.IndexOfKey(key)
        if index == -1:
            index = images.Count
            images.Add(key, icon.bitmap)
        return index

    def _format_text(self, text: str) -> str:
        # Remove new lines.
        text = " ".join(text.splitlines())

        if not text:
            # ListView will remove "columns" (rows within items) with empty strings.
            return " "
        elif len(text) < 260 and str_pixels(text, self._hwnd) < self._tile_text_width:
            # cchTextMax is 260, so max string length is 259 + null_terminator.
            return text

        # If the  previous conditions are not satisfied, the text must be shortened
        # and "..." appended. So the max number of characters to check is 256.
        #
        # Implementing the following guess reduces computation time for long strings
        # by around two thirds.
        approx_index = min(divmod(self._tile_text_width, 11)[0], 256)

        if str_pixels(text[:approx_index] + "...", self._hwnd) <= self._tile_text_width:
            for i in range(approx_index + 1, min(256, len(text))):
                if str_pixels(text[:i] + "...", self._hwnd) > self._tile_text_width:
                    return text[: i - 1] + "..."
            return text[:256] + "..."
        else:
            for i in range(approx_index, 0, -1):
                if str_pixels(text[:i] + "...", self._hwnd) < self._tile_text_width:
                    return text[:i] + "..."
            return "..."

    def _new_item(self, index) -> tuple[tuple[str, str], int]:
        item = self._data[index]
        icon = self._columns[0].icon(item)
        missing_value = self.interface.missing_value

        new_item = (
            tuple(
                c_wchar_p(self._format_text(column.text(item, missing_value)))
                for column in self._columns
            ),
            -1 if icon is None else self._image_index(icon._impl),
        )

        # The item must immediately be stored in cache to prevent the c_wchar_p(str)
        # from being garbage collected.
        self._cache[index] = new_item

        return new_item

    def _retrieve_virtual_item(self, index):
        try:
            return self._cache[index]
        except KeyError:
            return self._new_item(index)

    def scroll_to_row(self, index):
        SendMessageW(self._hwnd, wc.LVM_ENSUREVISIBLE, index, False)

    def get_selection(self):
        return SendMessageW(self._hwnd, wc.LVM_GETNEXTITEM, -1, wc.LVNI_SELECTED)

    def update_data(self):
        SendMessageW(
            self._hwnd, wc.LVM_SETITEMCOUNT, WPARAM(len(self._data)), LPARAM(0)
        )
        self._cache = {}

    def change_source(self, source):
        self.update_data()

    def insert(self, index, item):
        self.update_data()

    def change(self, item):
        self.update_data()

    def remove(self, index, item):
        self.update_data()

    def clear(self):
        self.update_data()

    def set_primary_action_enabled(self, enabled):
        self.primary_action_enabled = enabled

    def set_secondary_action_enabled(self, enabled):
        self.secondary_action_enabled = enabled

    def set_refresh_enabled(self, enabled):
        self.refresh_enabled = enabled

    after_on_refresh = None
