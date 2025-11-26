import { Header } from "./Header";

interface MainLayoutProps {
	children: React.ReactNode;
}

export function MainLayout({ children }: MainLayoutProps) {
	return (
		<div className="min-h-screen flex flex-col bg-white dark:bg-zinc-950 animate-fade-in transition-colors duration-300">
			<Header />
			<main className="flex-1 w-full">
				<div className="max-w-6xl mx-auto px-6 md:px-12 py-8">{children}</div>
			</main>
		</div>
	);
}
