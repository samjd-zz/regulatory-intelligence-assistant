import { LayoutDashboard, Moon, Search, MessageSquare, ShieldCheck, Sun, Languages } from "lucide-react";
import { Link, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { useTheme } from "@/context/ThemeContext";
import { useLanguageStore } from "@/store/languageStore";
import { useLanguageSync } from "@/hooks/useLanguageSync";

export function Header() {
	const location = useLocation();
	const { theme, toggleTheme } = useTheme();
	const { language, setLanguage } = useLanguageStore();
	const { t } = useTranslation();
	
	// Sync i18n with language store
	useLanguageSync();

	const navItems = [
		{ path: "/", label: t('nav.dashboard'), icon: LayoutDashboard },
		{ path: "/search", label: t('nav.search'), icon: Search },
		{ path: "/chat", label: t('nav.chat'), icon: MessageSquare },
		{ path: "/compliance", label: t('nav.compliance'), icon: ShieldCheck },
	];

	const isActive = (path: string) => {
		return location.pathname === path;
	};

	const toggleLanguage = () => {
		setLanguage(language === 'en' ? 'fr' : 'en');
	};

	return (
		<header className="border-b border-slate-100 dark:border-zinc-800 z-20 bg-white/95 dark:bg-zinc-950/95 backdrop-blur-sm sticky top-0 transition-colors duration-300">
			<div className="max-w-6xl mx-auto px-6 md:px-12 py-5 flex justify-between items-end">
				<div>
					<Link to="/">
						<h1 className="text-lg font-light text-slate-900 dark:text-zinc-50 tracking-tight hover:text-teal-600 dark:hover:text-teal-400 transition-colors cursor-pointer animate-slide-up delay-100">
							<span className="underline decoration-teal-500 underline-offset-4">
								R
							</span>
							egulatory{" "}
							<span className="underline decoration-teal-500 underline-offset-4">
								I
							</span>
							ntelligence
						</h1>
					</Link>
				</div>
				{/* Tab Navigation */}
				<nav className="flex gap-10 items-center animate-slide-up delay-200">
					{navItems.map((item) => {
						const Icon = item.icon;
						return (
							<Link
								key={item.path}
								to={item.path}
								className={`nav-btn ${isActive(item.path) ? "active" : ""} flex items-center gap-2`}
							>
								<Icon className="w-4 h-4" />
								{item.label}
							</Link>
						);
					})}
					<button
						type="button"
						onClick={toggleLanguage}
						className="flex items-center gap-2 px-3 py-2 rounded-full hover:bg-slate-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer focus:outline-none text-sm font-medium text-slate-700 dark:text-zinc-300"
						aria-label="Toggle language"
						title={language === 'en' ? 'Switch to French' : 'Passer à l\'anglais'}
					>
						<Languages className="w-4 h-4" />
						<span className="uppercase">{language}</span>
					</button>
					<button
						type="button"
						onClick={toggleTheme}
						className="p-2 rounded-full hover:bg-slate-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer focus:outline-none"
						aria-label="Toggle theme"
					>
						<div className="relative w-5 h-5">
							<Sun
								className={`w-5 h-5 text-slate-900 dark:text-zinc-100 absolute top-0 left-0 transition-all duration-500 ${theme === "dark" ? "opacity-0 rotate-90 scale-0" : "opacity-100 rotate-0 scale-100"}`}
							/>
							<Moon
								className={`w-5 h-5 text-slate-900 dark:text-zinc-100 absolute top-0 left-0 transition-all duration-500 ${theme === "light" ? "opacity-0 -rotate-90 scale-0" : "opacity-100 rotate-0 scale-100"}`}
							/>
						</div>
					</button>
				</nav>
			</div>
		</header>
	);
}
