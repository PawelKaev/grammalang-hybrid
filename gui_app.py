"""
gui_app.py
GrammaLang Hybrid v0.5.0 — GUI с темпоральной кардиограммой.
Открывает отдельное окно для визуализации графика.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import threading
import json
import os
from pathlib import Path

# Импорты ядра
from src.fast_parser import fast_parse
from src.deep_interpreter import deep_interpret, deep_interpret_heidegger, deep_interpret_dostoevsky
from src.fusion import apply_fusion_layer, build_temporal_cardiogram, build_ascii_cardiogram
from src.cardiogram import plot_cardiogram, save_cardiogram_png


class GrammaLangGUI:
    """Главное окно приложения GrammaLang Hybrid v0.5.0."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("GrammaLang Hybrid v0.5.0 — Онтологический анализатор")
        self.root.geometry("1100x800")
        self.root.minsize(900, 600)
        
        # Настройка стилей
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self._configure_styles()
        
        # Переменные состояния
        self.status_var = tk.StringVar(value="Готов. Режим: Аристотель | Движок: локальный Qwen")
        self.mode_var = tk.StringVar(value="aristotle")
        self.engine_var = tk.StringVar(value="local_qwen")
        self.output_mode_var = tk.StringVar(value="full")
        
        # Кэш для кардиограммы
        self._batch_results = None
        
        self._create_widgets()
        self._log_gui("GrammaLang Hybrid v0.5.0 запущен.")
        self._log_gui("Темпоральная кардиограмма активирована.")
    
    def _configure_styles(self):
        """Настройка тёмной темы Catppuccin Mocha."""
        bg = '#1e1e2e'
        fg = '#cdd6f4'
        accent = '#89b4fa'
        
        self.root.configure(bg=bg)
        self.style.configure('TFrame', background=bg)
        self.style.configure('TLabel', background=bg, foreground=fg, font=('Segoe UI', 10))
        self.style.configure('TButton', background='#313244', foreground=fg, font=('Segoe UI', 10),
                             borderwidth=1, padding=6)
        self.style.map('TButton', background=[('active', '#45475a')])
        self.style.configure('TNotebook', background=bg, borderwidth=0)
        self.style.configure('TNotebook.Tab', background='#313244', foreground=fg, padding=[12, 6],
                             font=('Segoe UI', 10, 'bold'))
        self.style.map('TNotebook.Tab', background=[('selected', '#45475a')])
        self.style.configure('TRadiobutton', background=bg, foreground=fg, font=('Segoe UI', 10))
        self.style.configure('TCombobox', fieldbackground='#313244', foreground=fg, font=('Segoe UI', 10))
        self.style.configure('TEntry', fieldbackground='#313244', foreground=fg, font=('Segoe UI', 10))
        self.style.configure('TLabelframe', background=bg, foreground=fg)
        self.style.configure('TLabelframe.Label', background=bg, foreground=fg, font=('Segoe UI', 10, 'bold'))
    
    def _create_widgets(self):
        """Создание всех виджетов интерфейса."""
        # Верхняя панель настроек
        settings_frame = ttk.Frame(self.root, padding=10)
        settings_frame.pack(fill=tk.X)
        
        # Режим анализа
        ttk.Label(settings_frame, text="Режим:").pack(side=tk.LEFT, padx=(0, 5))
        mode_combo = ttk.Combobox(settings_frame, textvariable=self.mode_var, width=18, state='readonly')
        mode_combo['values'] = ('aristotle', 'heidegger', 'dostoevsky')
        mode_combo.pack(side=tk.LEFT, padx=(0, 20))
        
        # Движок
        ttk.Label(settings_frame, text="Движок:").pack(side=tk.LEFT, padx=(0, 5))
        engine_combo = ttk.Combobox(settings_frame, textvariable=self.engine_var, width=18, state='readonly')
        engine_combo['values'] = ('local_qwen', 'local_deepseek', 'deepseek_api')
        engine_combo.pack(side=tk.LEFT, padx=(0, 20))
        
        # Режим вывода
        ttk.Label(settings_frame, text="Вывод:").pack(side=tk.LEFT, padx=(0, 5))
        output_combo = ttk.Combobox(settings_frame, textvariable=self.output_mode_var, width=14, state='readonly')
        output_combo['values'] = ('full', 'text_only', 'json_only')
        output_combo.pack(side=tk.LEFT, padx=(0, 10))
        
        # Вкладки
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Вкладка 1: Анализ
        self.analysis_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.analysis_tab, text="📝 Анализ")
        self._create_analysis_tab()
        
        # Вкладка 2: Кардиограмма
        self.cardiogram_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.cardiogram_tab, text="📈 Кардиограмма")
        self._create_cardiogram_tab()
        
        # Нижняя строка статуса
        status_bar = ttk.Frame(self.root, padding=5)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        ttk.Label(status_bar, textvariable=self.status_var, font=('Segoe UI', 9)).pack(side=tk.LEFT)
        ttk.Label(status_bar, text="v0.5.0", font=('Segoe UI', 9)).pack(side=tk.RIGHT)
    
    def _create_analysis_tab(self):
        """Вкладка анализа текста."""
        # Поле ввода
        input_frame = ttk.LabelFrame(self.analysis_tab, text="Введите текст для анализа:", padding=5)
        input_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.input_text = scrolledtext.ScrolledText(
            input_frame, height=10, wrap=tk.WORD,
            bg='#313244', fg='#cdd6f4', insertbackground='white',
            font=('Consolas', 11), relief=tk.FLAT, borderwidth=5
        )
        self.input_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Кнопки
        btn_frame = ttk.Frame(self.analysis_tab, padding=5)
        btn_frame.pack(fill=tk.X)
        
        self.btn_analyze = ttk.Button(btn_frame, text="🔍 Анализировать", command=self._on_analyze)
        self.btn_analyze.pack(side=tk.LEFT, padx=3)
        
        self.btn_batch = ttk.Button(btn_frame, text="📊 По предложениям", command=self._on_batch)
        self.btn_batch.pack(side=tk.LEFT, padx=3)
        
        self.btn_paste = ttk.Button(btn_frame, text="📋 Вставить", command=self._on_paste)
        self.btn_paste.pack(side=tk.LEFT, padx=3)
        
        self.btn_clear = ttk.Button(btn_frame, text="🗑 Очистить", command=self._on_clear)
        self.btn_clear.pack(side=tk.LEFT, padx=3)
        
        # Поле вывода
        output_frame = ttk.LabelFrame(self.analysis_tab, text="Результат анализа:", padding=5)
        output_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.output_text = scrolledtext.ScrolledText(
            output_frame, height=20, wrap=tk.WORD,
            bg='#1a1a2e', fg='#cdd6f4', insertbackground='white',
            font=('Consolas', 11), relief=tk.FLAT, borderwidth=5
        )
        self.output_text.pack(fill=tk.BOTH, expand=True, pady=5)
    
    def _create_cardiogram_tab(self):
        """Вкладка темпоральной кардиограммы."""
        # Верхняя панель с информацией
        info_frame = ttk.Frame(self.cardiogram_tab, padding=10)
        info_frame.pack(fill=tk.X)
        
        ttk.Label(info_frame, text="Темпоральная кардиограмма",
                  font=('Segoe UI', 14, 'bold')).pack(anchor=tk.W)
        ttk.Label(info_frame, text="Динамика индекса воли по предложениям. Выявляет тренды, зоны риска и паттерны.",
                  font=('Segoe UI', 9), foreground='#a6adc8').pack(anchor=tk.W)
        
        # Кнопки управления
        ctrl_frame = ttk.Frame(self.cardiogram_tab, padding=5)
        ctrl_frame.pack(fill=tk.X)
        
        self.btn_build_cardiogram = ttk.Button(
            ctrl_frame, text="📈 Построить кардиограмму",
            command=self._on_build_cardiogram
        )
        self.btn_build_cardiogram.pack(side=tk.LEFT, padx=3)
        
        self.btn_save_png = ttk.Button(
            ctrl_frame, text="💾 Сохранить PNG",
            command=self._on_save_cardiogram_png
        )
        self.btn_save_png.pack(side=tk.LEFT, padx=3)
        
        self.btn_show_ascii = ttk.Button(
            ctrl_frame, text="📋 Показать ASCII",
            command=self._on_show_ascii_cardiogram
        )
        self.btn_show_ascii.pack(side=tk.LEFT, padx=3)
        
        self.cardiogram_status = tk.StringVar(value="Нажмите «Построить кардиограмму» после пакетного анализа.")
        ttk.Label(ctrl_frame, textvariable=self.cardiogram_status,
                  font=('Segoe UI', 9), foreground='#a6adc8').pack(side=tk.RIGHT, padx=10)
        
        # Плейсхолдер
        self.cardiogram_placeholder = tk.Label(
            self.cardiogram_tab,
            text="Кардиограмма будет открыта в отдельном окне\n\n"
                 "1. Перейдите на вкладку «📝 Анализ»\n"
                 "2. Нажмите «📊 По предложениям»\n"
                 "3. Вернитесь сюда и нажмите «📈 Построить кардиограмму»",
            bg='#1e1e2e', fg='#6c7086', font=('Segoe UI', 12), justify=tk.CENTER
        )
        self.cardiogram_placeholder.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    
    # ============================================================
    # Обработчики кнопок
    # ============================================================
    
    def _on_analyze(self):
        """Анализ всего текста."""
        text = self.input_text.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("Пустой ввод", "Введите текст для анализа.")
            return
        
        self._disable_buttons()
        self.output_text.delete("1.0", tk.END)
        self.status_var.set("Анализирую...")
        threading.Thread(target=self._run_analysis, args=(text,), daemon=True).start()
    
    def _on_batch(self):
        """Пакетный анализ по предложениям."""
        text = self.input_text.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("Пустой ввод", "Введите текст для анализа.")
            return
        
        self._disable_buttons()
        self.output_text.delete("1.0", tk.END)
        self._batch_results = None
        self.status_var.set("Анализирую по предложениям...")
        threading.Thread(target=self._run_batch, args=(text,), daemon=True).start()
    
    def _on_paste(self):
        """Вставка из буфера обмена."""
        try:
            text = self.root.clipboard_get()
            self.input_text.delete("1.0", tk.END)
            self.input_text.insert("1.0", text)
        except Exception:
            messagebox.showwarning("Ошибка", "Не удалось вставить из буфера обмена.")
    
    def _on_clear(self):
        """Очистка полей."""
        self.input_text.delete("1.0", tk.END)
        self.output_text.delete("1.0", tk.END)
        self._batch_results = None
        self.status_var.set("Готов. Режим: Аристотель | Движок: локальный Qwen")
    
    def _on_build_cardiogram(self):
        """Построение кардиограммы из кэшированных результатов."""
        if not self._batch_results:
            messagebox.showwarning("Нет данных", 
                                   "Сначала выполните пакетный анализ («📊 По предложениям») на вкладке «Анализ».")
            return
        
        self.status_var.set("Строю кардиограмму...")
        try:
            cardiogram_data = build_temporal_cardiogram(self._batch_results)
            self._display_cardiogram(cardiogram_data)
            self.cardiogram_status.set(f"Готово. Тренд: {cardiogram_data.get('trend', 'N/A')} | "
                                       f"Среднее: {cardiogram_data.get('mean', 0):+.3f}")
            self.status_var.set("Кардиограмма построена.")
        except Exception as e:
            self._log_gui(f"Ошибка: {e}")
            messagebox.showerror("Ошибка", f"Не удалось построить кардиограмму:\n{e}")
            self.status_var.set("Ошибка построения кардиограммы.")
    
    def _on_save_cardiogram_png(self):
        """Сохранение кардиограммы в PNG."""
        if not self._batch_results:
            messagebox.showwarning("Нет данных", "Сначала выполните пакетный анализ.")
            return
        
        cardiogram_data = build_temporal_cardiogram(self._batch_results)
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
            initialfile="cardiogram.png"
        )
        
        if filepath:
            try:
                path = save_cardiogram_png(cardiogram_data, filepath)
                self._log_gui(f"Кардиограмма сохранена: {path}")
                self.cardiogram_status.set(f"Сохранено: {path}")
                messagebox.showinfo("Сохранено", f"Кардиограмма сохранена в:\n{path}")
            except Exception as e:
                self._log_gui(f"Ошибка сохранения: {e}")
                messagebox.showerror("Ошибка", f"Не удалось сохранить:\n{e}")
    
    def _on_show_ascii_cardiogram(self):
        """Показать ASCII-кардиограмму в отдельном окне."""
        if not self._batch_results:
            messagebox.showwarning("Нет данных", "Сначала выполните пакетный анализ.")
            return
        
        cardiogram_data = build_temporal_cardiogram(self._batch_results)
        ascii_art = build_ascii_cardiogram(cardiogram_data)
        
        # Отдельное окно для ASCII
        ascii_window = tk.Toplevel(self.root)
        ascii_window.title("ASCII-кардиограмма — GrammaLang v0.5")
        ascii_window.geometry("950x700")
        ascii_window.minsize(700, 400)
        ascii_window.configure(bg='#1a1a2e')
        
        # Заголовок
        header = ttk.Frame(ascii_window, padding=10)
        header.pack(fill=tk.X)
        ttk.Label(header, text="ASCII-кардиограмма",
                  font=('Segoe UI', 14, 'bold')).pack(side=tk.LEFT)
        
        # Статистика
        stats_text = (f"Среднее: {cardiogram_data.get('mean', 0):+.3f} | "
                      f"Тренд: {cardiogram_data.get('trend', 'N/A')} | "
                      f"Волатильность: {cardiogram_data.get('volatility', 0):.3f}")
        ttk.Label(header, text=stats_text, font=('Segoe UI', 9),
                  foreground='#a6adc8').pack(side=tk.RIGHT)
        
        # Текстовое поле
        text_frame = ttk.Frame(ascii_window, padding=5)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        text_widget = scrolledtext.ScrolledText(
            text_frame, wrap=tk.NONE,
            bg='#1a1a2e', fg='#cdd6f4',
            font=('Consolas', 11),
            relief=tk.FLAT, borderwidth=5
        )
        text_widget.pack(fill=tk.BOTH, expand=True)
        text_widget.insert("1.0", ascii_art)
        text_widget.configure(state='disabled')
        
        # Кнопки
        btn_frame = ttk.Frame(ascii_window, padding=10)
        btn_frame.pack(fill=tk.X)
        
        def copy_to_clipboard():
            ascii_window.clipboard_clear()
            ascii_window.clipboard_append(ascii_art)
            messagebox.showinfo("Скопировано", "ASCII-кардиограмма скопирована в буфер обмена.")
        
        ttk.Button(btn_frame, text="📋 Копировать", command=copy_to_clipboard).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="✕ Закрыть", command=ascii_window.destroy).pack(side=tk.RIGHT, padx=5)
        
        # Центрирование
        ascii_window.update_idletasks()
        w = ascii_window.winfo_width()
        h = ascii_window.winfo_height()
        sw = ascii_window.winfo_screenwidth()
        sh = ascii_window.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        ascii_window.geometry(f"+{x}+{y}")
        
        ascii_window.focus_force()
    
    # ============================================================
    # Фоновые задачи
    # ============================================================
    
    def _run_analysis(self, text):
        """Фоновый анализ одного текста."""
        try:
            self._log_gui("▸ Синтаксический анализ...")
            syntax = fast_parse(text)
            
            self._log_gui("▸ Семантический анализ...")
            h = deep_interpret(text, syntax)
            
            self._log_gui("▸ Слияние слоёв...")
            fusion = apply_fusion_layer(syntax, h)
            
            output = self._format_output(fusion)
            self.root.after(0, lambda: self._show_result(output))
        except Exception as e:
            self.root.after(0, lambda: self._on_error(str(e)))
    
    def _run_batch(self, text):
        """Фоновый пакетный анализ по предложениям."""
        try:
            # Разбиение на предложения
            delimiters = ['.', '!', '?', ';', '\n']
            sentences = []
            current = ""
            for char in text:
                current += char
                if char in delimiters:
                    stripped = current.strip()
                    if stripped and len(stripped) > 1:
                        sentences.append(stripped)
                    current = ""
            if current.strip() and len(current.strip()) > 1:
                sentences.append(current.strip())
            
            if not sentences:
                self.root.after(0, lambda: self._on_error("Не удалось разбить текст на предложения."))
                return
            
            self._log_gui(f"▸ Найдено предложений: {len(sentences)}")
            
            results = []
            for i, sentence in enumerate(sentences, 1):
                self._log_gui(f"▸ Предложение {i}/{len(sentences)}: {sentence[:50]}...")
                try:
                    syntax = fast_parse(sentence)
                    h = deep_interpret(sentence, syntax)
                    fusion = apply_fusion_layer(syntax, h)
                    fusion["sentence"] = sentence
                    fusion["sentence_num"] = i
                    results.append(fusion)
                except Exception as e:
                    self._log_gui(f"  ⚠ Ошибка в предложении {i}: {e}")
                    results.append({
                        "sentence": sentence,
                        "sentence_num": i,
                        "final_index": 0.0,
                        "health_status": "error",
                        "syntax": {"type": "unknown"},
                        "error": str(e)
                    })
            
            self._batch_results = results
            
            # Формирование вывода
            lines = [f"ПАКЕТНЫЙ АНАЛИЗ: {len(sentences)} предложений", "=" * 60]
            for r in results:
                status = r.get("health_status", "unknown")
                if status == "stable":
                    status_icon = "🟢"
                elif status == "high_stability":
                    status_icon = "🟢"
                elif status == "critical":
                    status_icon = "🔴"
                else:
                    status_icon = "⚪"
                
                idx = r.get("final_index", 0)
                sent = r.get("sentence", "")[:60]
                lines.append(f"{status_icon} [{r.get('sentence_num', '?'):2d}] {idx:+.3f} | {sent}...")
            
            lines.append("=" * 60)
            lines.append(f"\n✅ Анализ завершён. Перейдите на вкладку «📈 Кардиограмма» для визуализации.")
            
            output = "\n".join(lines)
            self.root.after(0, lambda: self._show_result(output))
        except Exception as e:
            self.root.after(0, lambda: self._on_error(str(e)))
    
    # ============================================================
    # Отображение результатов
    # ============================================================
    
    def _format_output(self, fusion):
        """Форматирование вывода в зависимости от режима."""
        mode = self.output_mode_var.get()
        
        if mode == "json_only":
            return json.dumps({
                "final_index": fusion.get("final_index"),
                "health_status": fusion.get("health_status"),
                "syntax_type": fusion.get("syntax", {}).get("type"),
                "dasein_mode": fusion.get("dasein_mode")
            }, ensure_ascii=False, indent=2)
        elif mode == "text_only":
            return fusion.get("analysis_text", "Нет текстового разбора.")
        else:
            # full
            text = fusion.get("analysis_text", "")
            text += "\n\n--- JSON ---\n"
            json_data = {k: v for k, v in fusion.items() if k != "analysis_text"}
            text += json.dumps(json_data, ensure_ascii=False, indent=2)
            return text
    
    def _show_result(self, output):
        """Отображение результата в GUI."""
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert("1.0", output)
        self._enable_buttons()
        self.status_var.set("Анализ завершён.")
    
    def _display_cardiogram(self, cardiogram_data):
        """
        Открывает отдельное окно с визуальной кардиограммой.
        С панелью инструментов matplotlib (зум, сохранение, навигация).
        """
        try:
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
            
            # Создаём новое окно
            plot_window = tk.Toplevel(self.root)
            plot_window.title("Темпоральная кардиограмма — GrammaLang v0.5")
            plot_window.geometry("1200x750")
            plot_window.minsize(800, 500)
            plot_window.configure(bg='#1a1a2e')
            
            # Фрейм для графика
            plot_frame = ttk.Frame(plot_window)
            plot_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(5, 0))
            
            # Строим фигуру
            total_points = cardiogram_data.get('total_points', 0)
            fig = plot_cardiogram(
                cardiogram_data,
                title=f"Темпоральная кардиограмма текста ({total_points} предложений)"
            )
            
            # Встраиваем canvas
            canvas = FigureCanvasTkAgg(fig, master=plot_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
            # Тулбар matplotlib (зум, перемещение, сохранение)
            toolbar_frame = ttk.Frame(plot_window)
            toolbar_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
            
            toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
            toolbar.update()
            toolbar.pack(fill=tk.X)
            
            # Информационная панель
            info_frame = ttk.Frame(plot_window, padding=10)
            info_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
            
            mean_val = cardiogram_data.get('mean', 0)
            trend = cardiogram_data.get('trend', 'N/A')
            volatility = cardiogram_data.get('volatility', 0)
            critical_count = len(cardiogram_data.get('critical_points', []))
            break_count = len(cardiogram_data.get('stability_break_points', []))
            patterns_count = len(cardiogram_data.get('patterns', []))
            
            trend_icon = "↗" if trend == "rising" else "↘" if trend == "falling" else "→"
            
            info_text = (
                f"Средний индекс: {mean_val:+.3f}  |  "
                f"Тренд: {trend_icon} {trend}  |  "
                f"Волатильность: {volatility:.3f}  |  "
                f"Критических: {critical_count}  |  "
                f"Сломов: {break_count}  |  "
                f"Паттернов: {patterns_count}"
            )
            
            ttk.Label(info_frame, text=info_text, font=('Segoe UI', 10),
                      foreground='#cdd6f4').pack(side=tk.LEFT)
            
            # Кнопка сохранения PNG
            def save_png():
                filepath = filedialog.asksaveasfilename(
                    parent=plot_window,
                    defaultextension=".png",
                    filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
                    initialfile="cardiogram.png"
                )
                if filepath:
                    path = save_cardiogram_png(cardiogram_data, filepath)
                    self._log_gui(f"Кардиограмма сохранена: {path}")
                    messagebox.showinfo("Сохранено", f"Кардиограмма сохранена в:\n{path}", parent=plot_window)
            
            ttk.Button(info_frame, text="💾 Сохранить PNG", command=save_png).pack(side=tk.RIGHT, padx=5)
            ttk.Button(info_frame, text="✕ Закрыть", command=plot_window.destroy).pack(side=tk.RIGHT, padx=5)
            
            # Центрируем окно
            plot_window.update_idletasks()
            w = plot_window.winfo_width()
            h = plot_window.winfo_height()
            sw = plot_window.winfo_screenwidth()
            sh = plot_window.winfo_screenheight()
            x = (sw - w) // 2
            y = (sh - h) // 2
            plot_window.geometry(f"+{x}+{y}")
            
            # Фокус на новое окно
            plot_window.focus_force()
            
            self._log_gui("Визуальная кардиограмма открыта в отдельном окне.")
            
        except ImportError as e:
            self._log_gui(f"⚠ Ошибка импорта matplotlib: {e}. Использую ASCII-версию.")
            self._on_show_ascii_cardiogram()
        except Exception as e:
            self._log_gui(f"Ошибка отображения графика: {e}")
            messagebox.showerror("Ошибка", f"Не удалось построить график:\n{e}")
    
    def _on_error(self, msg):
        """Обработка ошибок."""
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert("1.0", f"ОШИБКА:\n{msg}")
        self._enable_buttons()
        self.status_var.set("Ошибка анализа.")
    
    def _disable_buttons(self):
        """Блокировка кнопок на время анализа."""
        self.btn_analyze.configure(state='disabled')
        self.btn_batch.configure(state='disabled')
    
    def _enable_buttons(self):
        """Разблокировка кнопок."""
        self.btn_analyze.configure(state='normal')
        self.btn_batch.configure(state='normal')
    
    def _log_gui(self, message):
        """Логирование в статус и консоль."""
        print(f"[GrammaLang] {message}")
        self.root.after(0, lambda: self.status_var.set(message))


def main():
    """Точка входа."""
    root = tk.Tk()
    app = GrammaLangGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
