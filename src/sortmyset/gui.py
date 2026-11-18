from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .cli import main as cli_main
from .xml_library import load_library


def playlist_names(path: str) -> list[str]:
    if not path:
        return []
    try:
        library = load_library(path)
    except (OSError, ValueError, KeyError):
        return []
    return [
        str(item["Name"])
        for item in library.get("Playlists", [])
        if isinstance(item, dict) and item.get("Name")
    ]


class SortMySetWindow:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("SortMySet")
        self.root.geometry("680x520")
        self.root.minsize(620, 480)

        style = ttk.Style(root)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("Title.TLabel", font=("TkDefaultFont", 16, "bold"))
        style.configure("Action.TButton", padding=8)

        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.report_path = tk.StringVar()
        self.cache_path = tk.StringVar(value=str(Path("~/.cache/sortmyset").expanduser()))
        self.playlist_name = tk.StringVar()
        self.seed_text = tk.StringVar()
        self.random_seed = tk.BooleanVar(value=True)
        self.acquire_missing = tk.BooleanVar(value=False)
        self.musicnn_model = tk.StringVar(value="None")
        self.status_text = tk.StringVar(value="Выберите XML-файл Apple Music")

        self._build_interface()

    def _build_interface(self) -> None:
        outer = ttk.Frame(self.root, padding=20)
        outer.pack(fill="both", expand=True)

        ttk.Label(outer, text="SortMySet", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            outer,
            text="Упорядочивание Apple Music плейлиста по BPM, тональности, энергии и настроению",
        ).pack(anchor="w", pady=(2, 16))

        form = ttk.Frame(outer)
        form.pack(fill="x")

        self._path_row(form, "Входной XML", self.input_path, self._choose_input)
        self._path_row(form, "Выходной XML", self.output_path, self._choose_output)
        self._path_row(form, "JSON-отчёт", self.report_path, self._choose_report)

        options = ttk.Frame(outer)
        options.pack(fill="x", pady=(14, 10))

        ttk.Label(options, text="Плейлист").grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.playlist_combo = ttk.Combobox(
            options,
            textvariable=self.playlist_name,
            state="readonly",
            width=36,
        )
        self.playlist_combo.grid(row=0, column=1, sticky="w")

        ttk.Label(options, text="MusicNN").grid(row=1, column=0, sticky="w", pady=(10, 0), padx=(0, 8))
        ttk.Combobox(
            options,
            textvariable=self.musicnn_model,
            values=("None", "MTT_musicnn", "MSD_musicnn"),
            state="readonly",
            width=18,
        ).grid(row=1, column=1, sticky="w", pady=(10, 0))

        ttk.Checkbutton(
            options,
            text="Случайный seed",
            variable=self.random_seed,
            command=self._toggle_seed,
        ).grid(row=2, column=0, sticky="w", pady=(12, 0))
        self.seed_entry = ttk.Entry(options, textvariable=self.seed_text, width=20)
        self.seed_entry.grid(row=2, column=1, sticky="w", pady=(12, 0))
        self._toggle_seed()

        ttk.Checkbutton(
            options,
            text="Загружать отсутствующие треки",
            variable=self.acquire_missing,
        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(12, 0))

        ttk.Label(options, text="Кэш аудио").grid(row=4, column=0, sticky="w", pady=(12, 0), padx=(0, 8))
        ttk.Entry(options, textvariable=self.cache_path, width=36).grid(
            row=4, column=1, sticky="w", pady=(12, 0)
        )

        self.run_button = ttk.Button(
            outer,
            text="Сортировать плейлист",
            style="Action.TButton",
            command=self._run,
        )
        self.run_button.pack(pady=(16, 12))

        ttk.Label(
            outer,
            textvariable=self.status_text,
            wraplength=620,
            justify="left",
        ).pack(fill="x")

    def _path_row(
        self,
        parent: ttk.Frame,
        label: str,
        variable: tk.StringVar,
        browse: object,
    ) -> None:
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=(0, 8))
        ttk.Label(row, text=label, width=16).pack(side="left")
        ttk.Entry(row, textvariable=variable).pack(side="left", fill="x", expand=True, padx=(0, 8))
        ttk.Button(row, text="Выбрать", command=browse).pack(side="left")

    def _choose_input(self) -> None:
        path = filedialog.askopenfilename(
            title="Выберите XML-библиотеку",
            filetypes=(("Apple Music XML", "*.xml"), ("Все файлы", "*.*")),
        )
        if not path:
            return
        self.input_path.set(path)
        names = playlist_names(path)
        self.playlist_combo.configure(values=names)
        if names:
            self.playlist_name.set(names[0])
        if not self.output_path.get():
            source = Path(path)
            self.output_path.set(str(source.with_name(f"{source.stem}.sorted.xml")))
        if not self.report_path.get():
            source = Path(path)
            self.report_path.set(str(source.with_name(f"{source.stem}.report.json")))
        self.status_text.set(f"Найдено плейлистов: {len(names)}")

    def _choose_output(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Сохранить отсортированный XML",
            defaultextension=".xml",
            filetypes=(("Apple Music XML", "*.xml"),),
        )
        if path:
            self.output_path.set(path)

    def _choose_report(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Сохранить JSON-отчёт",
            defaultextension=".json",
            filetypes=(("JSON", "*.json"),),
        )
        if path:
            self.report_path.set(path)

    def _toggle_seed(self) -> None:
        if hasattr(self, "seed_entry"):
            if self.random_seed.get():
                self.seed_entry.configure(state="disabled")
            else:
                self.seed_entry.configure(state="normal")

    def _run(self) -> None:
        input_path = self.input_path.get().strip()
        output_path = self.output_path.get().strip()
        if not input_path:
            messagebox.showerror("Ошибка", "Выберите входной XML-файл.")
            return
        if not output_path:
            messagebox.showerror("Ошибка", "Выберите выходной XML-файл.")
            return
        if self.acquire_missing.get():
            if not messagebox.askyesno(
                "Подтверждение загрузки",
                "Разрешить поиск и скачивание недоступных треков? "
                "Пользователь отвечает за права и условия источников.",
            ):
                return

        arguments = [
            input_path,
            "--output",
            output_path,
        ]
        if self.playlist_name.get():
            arguments.extend(["--playlist", self.playlist_name.get()])
        if not self.random_seed.get():
            try:
                seed = int(self.seed_text.get().strip())
            except ValueError:
                messagebox.showerror("Ошибка", "Seed должен быть целым числом.")
                return
            arguments.extend(["--seed", str(seed)])
        if self.acquire_missing.get():
            arguments.append("--acquire-missing")
            arguments.extend(["--cache-dir", self.cache_path.get().strip()])
        if self.report_path.get().strip():
            arguments.extend(["--report", self.report_path.get().strip()])
        if self.musicnn_model.get() != "None":
            arguments.extend(["--musicnn", self.musicnn_model.get()])

        self.run_button.configure(state="disabled")
        self.status_text.set("Выполняется анализ и сортировка...")
        thread = threading.Thread(target=self._run_cli, args=(arguments,), daemon=True)
        thread.start()

    def _run_cli(self, arguments: list[str]) -> None:
        try:
            exit_code = cli_main(arguments)
            message = "Плейлист отсортирован." if exit_code == 0 else "Не удалось отсортировать плейлист."
        except Exception as exc:
            exit_code = 1
            message = f"Ошибка: {exc}"
        self.root.after(0, lambda: self._finish_run(exit_code, message))

    def _finish_run(self, exit_code: int, message: str) -> None:
        self.run_button.configure(state="normal")
        self.status_text.set(message)
        if exit_code == 0:
            messagebox.showinfo("Готово", f"{message}\n\nВыходной файл:\n{self.output_path.get()}")
        else:
            messagebox.showerror("Ошибка", message)


def run() -> None:
    root = tk.Tk()
    SortMySetWindow(root)
    root.mainloop()


def main() -> int:
    run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
