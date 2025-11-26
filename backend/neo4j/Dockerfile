# Custom Neo4j image with pre-installed plugins
FROM neo4j:5.15-community

# Install APOC plugin from labs
RUN cp /var/lib/neo4j/labs/apoc-*-core.jar /var/lib/neo4j/plugins/

# Download and install Graph Data Science plugin
RUN wget -q https://graphdatascience.ninja/neo4j-graph-data-science-2.6.9.jar \
    -O /var/lib/neo4j/plugins/graph-data-science.jar

# Set plugin permissions
RUN chmod 644 /var/lib/neo4j/plugins/*.jar

# Copy custom entrypoint wrapper
COPY docker-entrypoint-wrapper.sh /docker-entrypoint-wrapper.sh
RUN chmod +x /docker-entrypoint-wrapper.sh

# Use our wrapper as entrypoint
ENTRYPOINT ["/docker-entrypoint-wrapper.sh"]
CMD ["neo4j"]
