import { Header } from "./Header";

interface MainLayoutProps {
	children: React.ReactNode;
}

export function MainLayout({ children }: MainLayoutProps) {
	return (
		<div className="min-h-screen flex items-center justify-center p-6 md:p-12 bg-slate-50 animate-fade-in">
			<div className="w-full max-w-6xl bg-white border border-slate-200 shadow-xl shadow-slate-200/50 min-h-[800px] flex flex-col relative overflow-hidden transition-all duration-500">
				<Header />
				<main className="flex-1 relative">{children}</main>
			</div>
		</div>
	);
}
