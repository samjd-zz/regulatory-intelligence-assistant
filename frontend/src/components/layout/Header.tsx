import { Link, useLocation } from "react-router-dom";
import { Sun, Moon } from "lucide-react";
import { useTheme } from "@/context/ThemeContext";

export function Header() {
	const location = useLocation();
	const { theme, toggleTheme } = useTheme();

	const navItems = [
		{ path: "/", label: "Overview" },
		{ path: "/search", label: "Search" },
		{ path: "/chat", label: "Assistant" },
		{ path: "/compliance", label: "Compliance" },
	];

	const isActive = (path: string) => {
		return location.pathname === path;
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
					{navItems.map((item) => (
						<Link
							key={item.path}
							to={item.path}
							className={`nav-btn ${isActive(item.path) ? "active" : ""}`}
						>
							{item.label}
						</Link>
					))}
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
