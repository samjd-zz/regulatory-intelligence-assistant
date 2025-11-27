import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
	BrowserRouter as Router,
	Navigate,
	Route,
	Routes,
} from "react-router-dom";

import { MainLayout } from "@/components/layout/MainLayout";
import { ThemeProvider } from "@/context/ThemeContext";
import { Chat } from "@/pages/Chat";
import { ComplianceDynamic } from "@/pages/ComplianceDynamic";
import { Dashboard } from "@/pages/Dashboard";
import { Search } from "@/pages/Search";

// Create a client for React Query
const queryClient = new QueryClient({
	defaultOptions: {
		queries: {
			refetchOnWindowFocus: false,
			retry: 1,
			staleTime: 5 * 60 * 1000, // 5 minutes
		},
	},
});

function App() {
	return (
		<QueryClientProvider client={queryClient}>
			<ThemeProvider>
				<Router>
					<MainLayout>
						<Routes>
							<Route path="/" element={<Dashboard />} />
							<Route path="/search" element={<Search />} />
							<Route path="/chat" element={<Chat />} />
							<Route path="/compliance" element={<ComplianceDynamic />} />
							<Route path="*" element={<Navigate to="/" replace />} />
						</Routes>
					</MainLayout>
				</Router>
			</ThemeProvider>
		</QueryClientProvider>
	);
}

export default App;
