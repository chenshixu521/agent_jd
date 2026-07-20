FROM maven:3.9.9-eclipse-temurin-17 AS build

WORKDIR /workspace
COPY .mvn/settings.xml /root/.m2/settings.xml
COPY pom.xml ./
RUN --mount=type=cache,target=/root/.m2/repository \
    mvn -B -ntp dependency:go-offline

COPY src ./src
RUN --mount=type=cache,target=/root/.m2/repository \
    mvn -B -ntp -DskipTests package

FROM eclipse-temurin:17-jre-jammy

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system agentjd \
    && useradd --system --gid agentjd --home-dir /app --shell /usr/sbin/nologin agentjd \
    && mkdir -p /app/data/uploads \
    && chown -R agentjd:agentjd /app

WORKDIR /app
COPY --from=build --chown=agentjd:agentjd /workspace/target/agent-jd-java-*.jar /app/app.jar

USER agentjd
EXPOSE 8080

ENTRYPOINT ["java", "-XX:MaxRAMPercentage=75.0", "-jar", "/app/app.jar"]
