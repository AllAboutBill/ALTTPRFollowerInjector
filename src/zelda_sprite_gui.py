"""Simple GUI to reskin the ALTTP Zelda follower from a ZSPR sprite.

Pick a .zspr sprite and a .sfc ROM, choose mail color, and click "Update ROM".
It runs the same converter as zspr_to_zelda.py and writes a patched ROM, showing
a live preview of the four follower directions.

Run:  python npc_sprite/zelda_sprite_gui.py
(Tkinter ships with Python; no extra installs needed.)
"""
import os
import sys
import traceback
import webbrowser
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zspr_to_zelda as zz

APP_TITLE = "ALTTPR Follower Injector"
SPRITES_URL = "http://alttp.mymm1.com/sprites/"


def start_dir():
    """A friendly initial folder for file dialogs (Desktop, else home)."""
    desk = os.path.join(os.path.expanduser("~"), "Desktop")
    return desk if os.path.isdir(desk) else os.path.expanduser("~")


def default_out(rom_path, zspr_path):
    if not rom_path:
        return ""
    d, base = os.path.split(rom_path)
    stem, ext = os.path.splitext(base)
    tag = os.path.splitext(os.path.basename(zspr_path))[0] if zspr_path else "patched"
    return os.path.join(d, f"{stem}_{tag}{ext or '.sfc'}")


class App:
    def __init__(self, root):
        self.root = root
        root.title(APP_TITLE)
        root.minsize(580, 580)
        self._preview_img = None  # keep a ref so Tk doesn't GC it
        self._lastdir = start_dir()

        pad = dict(padx=8, pady=4)
        frm = ttk.Frame(root, padding=10)
        frm.grid(sticky="nsew")
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        frm.columnconfigure(1, weight=1)

        intro = ("Pick a sprite (.zspr) and your ROM (.sfc), then click Update ROM.\n"
                 "It writes a NEW patched ROM (your original is untouched) and shows a preview.")
        hdr = ttk.Frame(frm)
        hdr.grid(row=0, column=0, columnspan=3, sticky="w", padx=8, pady=(0, 8))
        ttk.Label(hdr, text=intro, foreground="#444", justify="left").pack(anchor="w")
        linkrow = ttk.Frame(hdr)
        linkrow.pack(anchor="w", pady=(4, 0))
        ttk.Label(linkrow, text="Need a sprite? Download .zspr files from ").pack(side="left")
        link = tk.Label(linkrow, text=SPRITES_URL, foreground="#1a5fb4", cursor="hand2",
                        font=("TkDefaultFont", 9, "underline"))
        link.pack(side="left")
        link.bind("<Button-1>", lambda _e: webbrowser.open(SPRITES_URL))

        self.zspr = tk.StringVar()
        self.rom = tk.StringVar()
        self.out = tk.StringVar()
        self.mail = tk.StringVar(value="green")
        self.recolor = tk.BooleanVar(value=True)
        self.pal = tk.StringVar(value="3 (free – recommended)")

        r = 1
        ttk.Label(frm, text="Sprite (.zspr):").grid(row=r, column=0, sticky="w", **pad)
        ttk.Entry(frm, textvariable=self.zspr).grid(row=r, column=1, sticky="ew", **pad)
        ttk.Button(frm, text="Browse…", command=self.pick_zspr).grid(row=r, column=2, **pad)

        r += 1
        ttk.Label(frm, text="ROM (.sfc):").grid(row=r, column=0, sticky="w", **pad)
        ttk.Entry(frm, textvariable=self.rom).grid(row=r, column=1, sticky="ew", **pad)
        ttk.Button(frm, text="Browse…", command=self.pick_rom).grid(row=r, column=2, **pad)

        r += 1
        ttk.Label(frm, text="Output ROM:").grid(row=r, column=0, sticky="w", **pad)
        ttk.Entry(frm, textvariable=self.out).grid(row=r, column=1, sticky="ew", **pad)
        ttk.Button(frm, text="Save as…", command=self.pick_out).grid(row=r, column=2, **pad)

        r += 1
        opt = ttk.Frame(frm)
        opt.grid(row=r, column=0, columnspan=3, sticky="w", **pad)
        ttk.Label(opt, text="Mail:").pack(side="left")
        ttk.Combobox(opt, textvariable=self.mail, values=["green", "blue", "red"],
                     width=8, state="readonly").pack(side="left", padx=(4, 16))
        ttk.Label(opt, text="Palette:").pack(side="left")
        ttk.Combobox(opt, textvariable=self.pal, width=20, state="readonly",
                     values=["3 (free – recommended)", "1", "2", "4 (shared – recolors others)"]
                     ).pack(side="left", padx=(4, 16))
        ttk.Checkbutton(opt, text="Write follower palette",
                        variable=self.recolor).pack(side="left")

        r += 1
        btns = ttk.Frame(frm)
        btns.grid(row=r, column=0, columnspan=3, sticky="w", **pad)
        ttk.Button(btns, text="Preview only", command=self.do_preview).pack(side="left")
        ttk.Button(btns, text="Update ROM", command=self.do_update).pack(side="left", padx=8)

        r += 1
        prevbox = ttk.LabelFrame(frm, text="Preview  (up · down · left · right)", padding=6)
        prevbox.grid(row=r, column=0, columnspan=3, sticky="nsew", **pad)
        frm.rowconfigure(r, weight=1)
        prevbox.columnconfigure(0, weight=1)
        prevbox.rowconfigure(0, weight=1)
        self.canvas = tk.Label(prevbox, background="#202028")
        self.canvas.grid(sticky="nsew")

        r += 1
        self.log = tk.Text(frm, height=7, wrap="word", state="disabled",
                           background="#111", foreground="#ddd")
        self.log.grid(row=r, column=0, columnspan=3, sticky="ew", **pad)

        # update suggested output path when inputs change
        self.zspr.trace_add("write", lambda *_: self.refresh_out())
        self.rom.trace_add("write", lambda *_: self.refresh_out())

    # ---- helpers -------------------------------------------------------
    def logln(self, msg):
        self.log.configure(state="normal")
        self.log.insert("end", str(msg) + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")
        self.root.update_idletasks()

    def refresh_out(self):
        # only auto-fill if user hasn't typed a custom path
        if not self.out.get() or self.out.get() == self._last_auto:
            self.out.set(default_out(self.rom.get(), self.zspr.get()))
            self._last_auto = self.out.get()

    _last_auto = ""

    def _remember(self, path):
        if path:
            self._lastdir = os.path.dirname(path)
        return path

    def pick_zspr(self):
        p = filedialog.askopenfilename(title="Choose a sprite (.zspr)",
                                       filetypes=[("ZSPR sprite", "*.zspr"), ("All files", "*.*")],
                                       initialdir=self._lastdir)
        if p:
            self.zspr.set(self._remember(p))

    def pick_rom(self):
        p = filedialog.askopenfilename(title="Choose the ROM (.sfc)",
                                       filetypes=[("SNES ROM", "*.sfc *.smc"), ("All files", "*.*")],
                                       initialdir=self._lastdir)
        if p:
            self.rom.set(self._remember(p))

    def pick_out(self):
        p = filedialog.asksaveasfilename(title="Save patched ROM as",
                                         defaultextension=".sfc",
                                         initialdir=self._lastdir,
                                         filetypes=[("SNES ROM", "*.sfc"), ("All files", "*.*")],
                                         initialfile=os.path.basename(default_out(self.rom.get(), self.zspr.get())))
        if p:
            self.out.set(self._remember(p))
            self._last_auto = ""  # user chose explicitly; stop auto-overwriting

    def show_preview(self, png):
        try:
            img = tk.PhotoImage(file=png)
            self._preview_img = img
            self.canvas.configure(image=img)
        except Exception as e:
            self.logln(f"(could not display preview: {e})")

    # ---- actions -------------------------------------------------------
    def _run(self, write):
        zspr, rom = self.zspr.get().strip(), self.rom.get().strip()
        if not zspr or not os.path.isfile(zspr):
            messagebox.showerror("Missing sprite", "Pick a valid .zspr file."); return
        if write and (not rom or not os.path.isfile(rom)):
            messagebox.showerror("Missing ROM", "Pick a valid ROM file."); return
        out = self.out.get().strip() if write else None
        pal = int(self.pal.get().split()[0])  # leading digit of the dropdown label
        try:
            res = zz.convert(rom or None, zspr, out, mail=self.mail.get(),
                             write_pal=self.recolor.get(), follower_pal=pal,
                             log=self.logln)
            self.show_preview(res["preview"])
            if write:
                self.logln(f"✓ done: {res['out_rom']}")
                messagebox.showinfo("Done", f"Updated ROM written:\n{res['out_rom']}")
        except Exception as e:
            self.logln(f"ERROR: {e}")
            traceback.print_exc()
            messagebox.showerror("Failed", str(e))

    def do_preview(self):
        self._run(write=False)

    def do_update(self):
        self._run(write=True)


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
