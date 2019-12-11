import axios, { AxiosInstance } from 'axios';

export class Client {
  private axios: AxiosInstance;

  constructor(baseURL: string) {
    this.axios = axios.create({
      baseURL,
    });
  }

  public get(path: string, params: {} = {}): Promise<any> {
    return new Promise((resolve, reject) => {
      this.axios.get(path, { params, })
        .then((resp) => {
          resolve(resp.data);
        })
        .catch((resp) => {
          reject(resp.response);
        });
    });
  }

  public post(path: string, params: {} = {}, headers: {} = {}): Promise<any> {
    return new Promise((resolve, reject) => {
      this.axios.post(path, params, { headers, })
        .then((resp) => {
          resolve(resp.data);
        })
        .catch((resp) => {
          reject(resp.response);
        });
    });
  }

  public delete(path: string, params: {} = {}): Promise<any> {
    return new Promise((resolve, reject) => {
      this.axios.delete(path, params)
        .then((resp) => {
          resolve(resp.data);
        })
        .catch((resp) => {
          reject(resp.response);
        });
    });
  }
}
