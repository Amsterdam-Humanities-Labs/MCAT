# MCAT Architecture

## System Overview

```mermaid
graph TB
    subgraph Desktop["pywebview Desktop Window"]
        subgraph Frontend["Svelte 5 Frontend"]
            subgraph Views["Views"]
                StartScreen
                ProjectWizard
                ProjectView
            end

            subgraph Stores["Stores (Svelte 5 Runes)"]
                appStore["appStore<br/>view, backendConnected"]
                projectStore["projectStore<br/>project, runs, loading"]
                processingStore["processingStore<br/>state, progress, statusCounts"]
                consoleStore["consoleStore<br/>messages[]"]
                wizardStore["wizardStore<br/>name, platform, csv_path"]
            end

            subgraph APILayer["API Layer"]
                apiClient["api client<br/>fetch() + retry"]
                sseListener["SSE listener<br/>EventSource /events"]
            end
        end

        subgraph Backend["Python Backend (ThreadingHTTPServer)"]
            subgraph HTTPServer["HTTP Server"]
                GET["GET handlers"]
                POST["POST handlers"]
                SSEEndpoint["SSE /events endpoint"]
            end

            subgraph Handlers["API Handlers"]
                projectHandler["project handler"]
                processingHandler["processing handler"]
                runHandler["run handler"]
                trackingHandler["tracking handler"]
                csvHandler["csv handler"]
                dialogHandler["dialog handler"]
            end

            subgraph Services["Services"]
                projectService["ProjectService"]
                processingService["ProcessingService"]
                runService["RunService"]
                trackingService["TrackingService"]
            end

            subgraph Core["Core"]
                batchProcessor["BatchProcessor<br/>ThreadPoolExecutor"]
                scrapers["Scrapers<br/>YouTube / Instagram / Mock"]
                dispatcher["PyDispatcher<br/>signal bus"]
                eventBus["EventBus<br/>SSE pub/sub"]
            end

            subgraph Models["Models"]
                projectConfig["ProjectConfig<br/>project.json"]
                runConfig["RunConfig"]
                processingJob["ProcessingJob"]
            end

            subgraph Storage["File System"]
                projectJSON["project.json"]
                urlsCSV["urls.csv"]
                runsFolder["runs/{id}/<br/>results.csv, changes.csv,<br/>combined.csv, screenshots/"]
            end
        end
    end
```

## Data Flow: User Action → Backend → SSE → UI Update

```mermaid
sequenceDiagram
    participant User
    participant View as ProjectView
    participant Store as Stores
    participant API as API Client
    participant Handler as HTTP Handler
    participant Service as Service Layer
    participant Core as BatchProcessor
    participant Bus as EventBus
    participant SSE as SSE Stream

    Note over User,SSE: === START PROCESSING ===

    User->>View: Click "Start"
    View->>Store: processingStore.start()
    Store->>API: POST /process/start
    API->>Handler: processingHandler.start()
    Handler->>Service: runService.start_run()
    Service->>Service: Create run folder + RunConfig
    Handler->>Service: processingService.start_processing(job)
    Service->>Core: spawn worker thread
    Handler-->>API: {status: ok}
    API-->>Store: response
    Core->>Core: batchProcessor.process_csv()

    Note over User,SSE: === PROGRESS UPDATES (per URL) ===

    loop For each URL (4 concurrent)
        Core->>Core: scraper.check_url(url)
        Core->>Core: write row → results.csv
        Core->>Service: dispatcher.send(PROGRESS)
        Service->>Handler: _on_processing_progress()
        Handler->>Bus: eventBus.publish({type: processing, ...})
        Bus->>SSE: event: processing\ndata: {state, processed, statusCounts}
        SSE->>Store: processingStore.updateFromSSE()
        Store->>View: reactive UI update
        View->>User: progress bar, counts, current URL
    end

    Note over User,SSE: === COMPLETION ===

    Core->>Service: dispatcher.send(COMPLETED)
    Service->>Handler: _on_processing_completed()
    Handler->>Service: runService.complete_run()
    Service->>Service: generate combined.csv + changes.csv
    Handler->>Bus: publish "processing" + "project" events
    Bus->>SSE: event: processing {state: completed}
    SSE->>Store: processingStore.updateFromSSE()
    Bus->>SSE: event: project {runs: [...updated]}
    SSE->>Store: projectStore.setProject()
    Store->>View: show completed run in Timeline
```

## SSE Event Flow

```mermaid
flowchart LR
    subgraph Backend Services
        PS[ProjectService]
        PRS[ProcessingService]
        TS[TrackingService]
        LB[LogBuffer]
    end

    subgraph EventBus
        EB((EventBus<br/>pub/sub))
    end

    subgraph SSE Stream
        SE[/GET /events/]
    end

    subgraph Frontend Stores
        pStore[projectStore]
        prStore[processingStore]
        cStore[consoleStore]
    end

    PS -->|"event: project<br/>{name, runs[], tracking}"| EB
    PRS -->|"event: processing<br/>{state, processed, statusCounts}"| EB
    TS -->|"event: tracking.started<br/>event: tracking.stopped"| EB
    TS -->|"event: project<br/>(next_check update)"| EB
    LB -->|"event: log<br/>{id, text, level}"| EB

    EB --> SE
    SE -->|project| pStore
    SE -->|processing| prStore
    SE -->|log| cStore
```

## API Endpoints

```mermaid
flowchart TD
    subgraph "POST Endpoints"
        subgraph Project
            PC["/project/create"]
            PO["/project/open"]
            PCL["/project/close"]
            PSS["/project/screenshots"]
            PTC["/project/tracking-config"]
            PIP["/project/import-preview"]
            PIC["/project/import-confirm"]
        end

        subgraph Processing
            PStart["/process/start"]
            PPause["/process/pause"]
            PResume["/process/resume"]
        end

        subgraph Run
            RA["/run/abandon"]
            RC["/run/changes"]
            RR["/run/results"]
        end

        subgraph Tracking
            TStart["/tracking/start"]
            TStop["/tracking/stop"]
            TStatus["/tracking/status"]
        end

        subgraph CSV
            CL["/csv/load"]
            CD["/csv/detect-url-column"]
        end

        subgraph Dialog["Dialog (Native OS)"]
            DOF["/dialog/open-file"]
            DOD["/dialog/open-folder"]
            DOE["/dialog/open-external"]
        end
    end

    subgraph "GET Endpoints"
        H["/health"]
        E["/events (SSE)"]
    end
```

## Processing Pipeline

```mermaid
flowchart TD
    Start["processingService.start_processing()"] --> Thread["Spawn Worker Thread"]
    Thread --> Load["Load urls.csv"]
    Load --> Init["Initialize Scraper"]

    Init --> Mock{MCAT_MOCK=1?}
    Mock -->|Yes| MS["MockScraper<br/>reads scenario.json"]
    Mock -->|No| Platform{Platform?}
    Platform -->|YouTube| YS["YouTubeScraper<br/>Selenium + Chrome"]
    Platform -->|Instagram| IS["InstagramScraper<br/>Selenium + Chrome"]

    MS --> Pool
    YS --> Pool
    IS --> Pool

    Pool["ThreadPoolExecutor<br/>max_workers=4"]
    Pool --> Process

    subgraph Process["Per URL"]
        Check["scraper.check_url(url)"]
        Check --> Status["Return status:<br/>Live / Removed / Restricted /<br/>Age-restricted / Private / Error"]
        Status --> Write["Write row → results.csv"]
        Write --> Signal["dispatcher.send(PROGRESS)"]
        Signal --> Pause{"pause_event<br/>cleared?"}
        Pause -->|Yes| Wait["Block until resumed"]
        Pause -->|No| Cancel{"cancel_flag<br/>set?"}
        Cancel -->|Yes| Abort["Return early"]
        Cancel -->|No| Next["Next URL"]
    end

    Process --> Complete["All URLs done"]
    Complete --> GenCSV["Generate changes.csv<br/>+ combined.csv"]
    GenCSV --> Done["dispatcher.send(COMPLETED)"]
```

## Tracking (Scheduled Runs)

```mermaid
sequenceDiagram
    participant User
    participant View as ProjectView
    participant API as API Client
    participant TS as TrackingService
    participant PS as ProcessingService
    participant Bus as EventBus

    User->>View: Enable tracking + set interval
    View->>API: POST /project/tracking-config
    User->>View: Click "Start"
    View->>API: POST /tracking/start {interval, unit}
    API->>TS: start_tracking()
    TS->>Bus: publish tracking.started
    TS->>TS: _schedule_next_check()
    TS->>TS: threading.Timer(interval_seconds)

    Note over TS: Timer fires after interval

    TS->>TS: _execute_tracking_run()
    TS->>PS: start_processing(job)
    PS->>PS: process all URLs...
    PS->>TS: dispatcher.send(COMPLETED)
    TS->>TS: complete_run()
    TS->>TS: _schedule_next_check()
    TS->>Bus: publish project (next_check updated)

    Note over TS: Repeats until stopped

    User->>View: Click "Stop" or close project
    View->>API: POST /tracking/stop
    API->>TS: stop_tracking()
    TS->>TS: cancel timer
    TS->>Bus: publish tracking.stopped
```

## Frontend Component Tree

```mermaid
flowchart TD
    App["App.svelte"]
    App -->|"view=start"| SS["StartScreen"]
    App -->|"view=wizard"| PW["ProjectWizard"]
    App -->|"view=project"| PV["ProjectView"]

    PV --> TB["Toolbar<br/>project name, url count, folder button"]
    PV --> CTRL["Controls"]
    PV --> PROG["ProgressSection"]
    PV --> TL["Timeline"]
    PV --> CP["ConsolePanel"]

    CTRL --> CSB["ControlsStartButton<br/>Start / Pause / Resume"]
    CTRL --> CI["ControlsInterval<br/>interval value + unit"]
    CTRL --> CB["Checkbox<br/>screenshots toggle"]
    CTRL --> CTS["ControlsTrackingStatus<br/>countdown / in-progress"]

    PROG --> PB["ProgressBar"]
    PROG --> PL["ProgressLegend<br/>status counts + deltas"]

    TL --> TR["TimelineRunning<br/>active run indicator"]
    TL --> TRow["TimelineRow<br/>dot, date, changes, transitions"]
    TL --> DP["DetailPanel"]

    DP --> DH["DetailHeader<br/>run folder button"]
    DP --> Tabs["Tabs"]
    Tabs --> DR["DetailRun<br/>run metadata"]
    Tabs --> DC["DetailChanges<br/>grouped transitions"]
    Tabs --> DRes["DetailResults<br/>DataTable"]

    CP --> CH["ConsoleHeader"]
    CP --> CBod["ConsoleBody"]
    CBod --> CE["ConsoleEntry<br/>log line"]
```

## Store → View Data Flow

```mermaid
flowchart LR
    subgraph "Svelte Stores ($state)"
        AS["appStore<br/>view"]
        PS["projectStore<br/>project, runs"]
        PRS["processingStore<br/>state, progress"]
        CS["consoleStore<br/>messages"]
    end

    subgraph "SSE Updates"
        SSE["EventSource /events"]
    end

    subgraph "API Calls (user-initiated)"
        APIout["fetch POST /..."]
    end

    SSE -->|"event: project"| PS
    SSE -->|"event: processing"| PRS
    SSE -->|"event: log"| CS

    PS -->|project, runs, baselineRun| PV["ProjectView"]
    PRS -->|state, progress, statusCounts| PV
    CS -->|messages| PV
    AS -->|view| App["App.svelte"]

    PV -->|"user actions"| APIout
    APIout -->|"triggers backend"| SSE
```
