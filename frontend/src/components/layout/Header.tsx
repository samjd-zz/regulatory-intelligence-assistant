import { Link, useLocation } from "react-router-dom";

export function Header() {
	const location = useLocation();

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
		<header className="flex justify-between items-end px-12 py-10 border-b border-slate-50 z-20 bg-white/80 backdrop-blur-sm sticky top-0">
			<div>
				<p className="text-[10px] font-bold tracking-widest text-slate-400 uppercase mb-1 animate-slide-up">
					Government of Canada
				</p>
				<h1 className="text-xl font-semibold text-slate-800 tracking-tight animate-slide-up delay-100">
					Regulatory Intelligence
				</h1>
			</div>
			{/* Tab Navigation */}
			<nav className="flex gap-10 animate-slide-up delay-200">
				{navItems.map((item) => (
					<Link
						key={item.path}
						to={item.path}
						className={`nav-btn ${isActive(item.path) ? "active" : ""}`}
					>
						{item.label}
					</Link>
				))}
			</nav>
		</header>
	);
}
