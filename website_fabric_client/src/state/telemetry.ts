import { v4 as uuidv4 } from "uuid";
import {
  EventPropertyBag,
  EndCertifiedEventActivityObject,
  TimedCertifiedEventEpicRequests,
  CertifiedEventEpicRequests,
  EventEpicRequests,
  IError,
  EndFailedCertifiedEventActivityFunc,
  EndEventPropertyBag,
  EndCertifiedEventActivityFunc,
  ActivityStatus,
  TelemetryEpicRequests,
} from "@trident/relational-db-ux/lib/types";

function getLogger() {
  return {
    logCertifiedEvent: (...rest) => {},
    startActivity: (...rest) => ({
      endActivity: (...rest) => {},
      endFailedActivity: (...rest) => {},
      correlationId: uuidv4(),
    }),
    info: (...rest) => {},
    warn: (...rest) => {},
    error: (...rest) => {},
    debug: (...rest) => {},
  };
}
export function createTimedCertifiedEventEpicRequests(): TimedCertifiedEventEpicRequests {
  return {
    startCertifiedEventActivity: (
      feature: string,
      activity: string,
      correlationId?: string,
      additionalAttributes?: EventPropertyBag
    ): EndCertifiedEventActivityObject => {
      const telemetryObject = getLogger().startActivity(
        feature,
        activity,
        correlationId ?? uuidv4(),
        {
          ...additionalAttributes,
        }
      );

      const endCertifiedEventActivity: EndCertifiedEventActivityFunc = (
        activityStatus: Exclude<ActivityStatus, ActivityStatus.Failed>,
        endAdditionalAttributes?: EndEventPropertyBag,
        traceProperties?: EventPropertyBag
      ) => {
        telemetryObject.endActivity(
          activityStatus,
          undefined,
          endAdditionalAttributes,
          traceProperties
        );
      };

      const endFailedCertifiedEventActivity: EndFailedCertifiedEventActivityFunc =
        (
          error: IError,
          endAdditionalAttributes?: EndEventPropertyBag,
          traceProperties?: EventPropertyBag
        ) => {
          telemetryObject.endFailedActivity(
            error,
            undefined,
            endAdditionalAttributes,
            traceProperties
          );
        };

      return {
        feature,
        activity,
        correlationId: telemetryObject.correlationId,
        endCertifiedEventActivity,
        endFailedCertifiedEventActivity,
      };
    },
  };
}
/** Request for logging certified events that do not have a duration */
export function createCertifiedEventEpicRequests(): CertifiedEventEpicRequests {
  return {
    logCertifiedEvent: function (
      feature: string,
      activity: string,
      additionalAttributes?: EventPropertyBag
    ): void {
      getLogger().logCertifiedEvent(feature, activity, additionalAttributes);
    },
  };
}

/** Request for logging events with freeform data, like GUIDs or stacktraces */
export function createLogEventEpicRequest(): EventEpicRequests {
  return {
    logInfo: (message: string, moduleName: string, details?: unknown) =>
      getLogger().info(message, details),
    logWarn: (
      message: string,
      moduleName: string,
      errorDetails?: unknown,
      sourceError?: unknown,
      messageDetails?: unknown
    ) => getLogger().warn(message, errorDetails, sourceError, messageDetails),
    logError: (
      message: string,
      moduleName: string,
      errorDetails?: unknown,
      originalError?: unknown,
      messageDetails?: unknown
    ) =>
      getLogger().error(message, errorDetails, originalError, messageDetails),
    logDebug: (message: string, _moduleName: string) =>
      getLogger().debug(message),
  };
}

// This object contains all the telemetry requests that can be used in epics
export function createTelemetryEpicRequests(): TelemetryEpicRequests {
  return {
    ...createTimedCertifiedEventEpicRequests(),
    ...createCertifiedEventEpicRequests(),
    ...createLogEventEpicRequest(),
    updateOpenArtifactActivityStatus: (
      artifactId,
      status,
      activityAttributes
    ) => {
      console.log({
        activityType: "openArtifact",
        artifactObjectId: artifactId,
        status: status,
        activityAttributes: activityAttributes,
      });
    },
  };
}
