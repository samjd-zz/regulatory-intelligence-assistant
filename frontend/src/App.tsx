import {
	BrowserRouter as Router,
	Routes,
	Route,
	Navigate,
} from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MainLayout } from "@/components/layout/MainLayout";
import { Dashboard } from "@/pages/Dashboard";
import { Search } from "@/pages/Search";
import { Chat } from "@/pages/Chat";
import { Compliance } from "@/pages/Compliance";

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
			<Router>
				<MainLayout>
					<Routes>
						<Route path="/" element={<Dashboard />} />
						<Route path="/search" element={<Search />} />
						<Route path="/chat" element={<Chat />} />
						<Route path="/compliance" element={<Compliance />} />
						<Route path="*" element={<Navigate to="/" replace />} />
					</Routes>
				</MainLayout>
			</Router>
		</QueryClientProvider>
	);
}

export default App;
