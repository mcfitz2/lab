import axios, { AxiosInstance, AxiosError } from "axios";

export interface FlowRun {
    id:                         string;
    created:                    Date;
    updated:                    Date;
    name:                       string;
    flow_id:                    string;
    state_id:                   string;
    deployment_id:              string;
    work_queue_id:              null;
    work_queue_name:            null;
    flow_version:               null;
    deployment_version:         string;
    idempotency_key:            string;
    tags:                       string[];
    parent_task_run_id:         null;
    state_type:                 string;
    state_name:                 string;
    run_count:                  number;
    expected_start_time:        Date;
    next_scheduled_start_time:  Date;
    start_time:                 null;
    end_time:                   null;
    total_run_time:             number;
    estimated_run_time:         number;
    estimated_start_time_delta: number;
    auto_scheduled:             boolean;
    infrastructure_document_id: null;
    infrastructure_pid:         null;
    work_pool_id:               null;
    work_pool_name:             null;
    state:                      State;
}

export interface State {
    id:            string;
    type:          string;
    name:          string;
    timestamp:     Date;
    message:       string;
    data:          null;
    state_details: StateDetails;
}

export interface StateDetails {
    flow_run_id:        null;
    task_run_id:        null;
    child_flow_run_id:  null;
    scheduled_time:     Date;
    cache_key:          null;
    cache_expiration:   null;
    untrackable_result: boolean;
    pause_timeout:      null;
    pause_reschedule:   boolean;
    pause_key:          null;
    run_input_keyset:   null;
    refresh_cache:      null;
    retriable:          null;
    transition_id:      null;
    task_parameters_id: null;
}


interface Variable {
    id: string;
    created: string;
    updated: string;
    name: string;
    value: string;
    tags: [string];
  }
  
  interface BlockDocument {
    id: string;
    name: string;
    data: {value: string};
    block_schema_id: string;
  
  }
  interface Secret {
    id: string;
    name: string;
    data: {value: string};
    block_schema_id: string;
  
  }
  interface BlockSchema {
    id: string
  }
  interface Deployment {
    name: string,
    id: string
  }
  class PrefectClient {
    client: AxiosInstance;
    accountId: string;
    workspaceId: string;
    constructor(accountId: string, workspaceId: string) {
      this.accountId = accountId;
      this.workspaceId = workspaceId;
      this.client = axios.create({
        baseURL: `https://api.prefect.cloud/api/accounts/${this.accountId}/workspaces/${this.workspaceId}`,
      });
      this.client.defaults.headers.common['Authorization'] = `Bearer ${process.env.PREFECT_API_KEY}`;
    }
    handleError(error: any) {
      let data
      if (error instanceof AxiosError) data = error?.response?.data
      else data = String(error)
      console.log(data) 
    }
    async getVariableByName(name: string): Promise<Variable> {
      let url = `/variables/name/${name}`
      let response = await this.client.get(url)
      return response.data as Variable
    }

    async getFlowRuns(deployment_ids: string[]): Promise<FlowRun[]> {
      let url = `/flow_runs/filter`
      let count = 0;
      let limit = 200;
      let offset = 0;
      let flowRuns = []
      var dateOffset = (24*60*60*1000) * 3;
      var since = new Date();
      since.setTime(since.getTime() - dateOffset);
      do {
          let body = {
            "sort": "START_TIME_DESC",
            "offset": offset,
            "deployments": {
                "id":{
                    "any_":deployment_ids
                }
            },
            flow_runs: {
                start_time: {
                    after_: since
                }
            },
            limit: limit
          }
          console.log('Calling', url, offset)
          let response = await this.client.post(url, body)
          flowRuns.push(...response.data)
          offset = offset + limit;
          count = response.data.length;
      } while (count > 0)
      console.log(`Found ${flowRuns.length} runs`)
      return flowRuns
    }

    async getDeployments(): Promise<Deployment[]> {
      let url = `/deployments/filter`
      let body = {
        "offset": 0
      }
      let response = await this.client.post(url, body)
      return response.data as FlowRun[]
    }


    async getBlockByTypeAndName(type: string, name: string): Promise<BlockDocument> {
  
      let url = `/block_types/slug/${type}/block_documents/name/${name}`
      let response = await this.client.get(url, {params: {include_secrets: true}})
      return response.data as BlockDocument
    }
  
    async getSecretByName(name: string): Promise<Secret> {
  
      let url = `/block_types/slug/secret/block_documents/name/${name}`
      let response = await this.client.get(url, {params: {include_secrets: true}})
      return response.data as Secret
    }
    async setSecret(id: string, schema_id: string, value:any): Promise<any> {
  
      let url = `/block_documents/${id}`
      try {
        let response = await this.client.patch(url, {block_schema_id: schema_id, data: {value: value}, merge_existing_data: false})
        return response.data
      } catch (error) {
        this.handleError(error)   
      }  
    }
    async setSecretByName(name: string, value:any): Promise<any> {
      let secret = await this.getSecretByName(name);
      let schema_id = secret.block_schema_id
      let id = secret.id;
      let url = `/block_documents/${id}`
      try {
        let response = await this.client.patch(url, {block_schema_id: schema_id, data: {value: value}, merge_existing_data: false})
        return response.data
      } catch (error) {
        this.handleError(error)   
      }  
    }
    async getBlockTypeBySlug(slug: string) {
      let url = `/block_types/slug/${slug}`
      try {
        let response = await this.client.get(url)
        return response.data
      } catch (error) {
        this.handleError(error)   
      }
    }
    async createSecretSchema(block_type_id: string): Promise<BlockSchema> {
  
      let url = `/block_schemas`
      try {
        let response = await this.client.post(url, {fields: {}, capabilities: ["string"], block_type_id: block_type_id})
        return response.data as BlockSchema
      } catch (error) {
        this.handleError(error)   
        return null as any;
      }  
    }
    async createSecret(name: string, value: string) {
      let block_type = await this.getBlockTypeBySlug("secret");
      let schema = await this.createSecretSchema(block_type.id)
      let url = `/block_documents`
      try {
        let response = await this.client.post(url, {name: name, data: {value: value}, block_type_id: block_type.id, block_schema_id: schema.id})
        return response.data
      } catch (error) {
        this.handleError(error)   
      }
    }
    async secretExists(name: string) {
      try {
        await this.getSecretByName(name)
        return true;
      } catch(error) {
        return false;
      }
    }
  
    async createOrUpdateSecret(name: string, value: string) {
      try {
        return await this.setSecretByName(name, value);
      } catch(error) {
        return await this.createSecret(name, value);
      }
    }
    async getLatestFlowRunPerDeployment() {
        let deployments = (await this.getDeployments()).reduce((map, deployment) => {
            map[deployment.id] = deployment.name
            return map;
        }, {})
        let results = await this.getFlowRuns(Object.keys(deployments));
        let latest = results.reduce((result, flowRun) => {
            if (flowRun.deployment_id) {
                let deploymentName = deployments[flowRun.deployment_id];
                if (!result[deploymentName] && flowRun.state_type != 'SCHEDULED') {
                    result[deploymentName] = flowRun.state_type
                }
            }
            return  result;
        }, {});
        return latest;
    }
  }

  export default PrefectClient;